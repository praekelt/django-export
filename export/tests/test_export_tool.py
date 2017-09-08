import json

from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase
from django.utils import six

from export import tools


class MockDjangoObject(models.Model):
    field1 = models.IntegerField()
    field2 = models.IntegerField()


class ToolsTestCase(TestCase):
    """
    Testcase for tools.Export.
    """
    def setUp(self):
        self.export = tools.Export(MockDjangoObject)
        self.obj = MockDjangoObject(field1=1, field2=2)

    def test_serialize(self):
        string_types = [str]
        if six.PY2:
            string_types = [unicode, basestring]
        self.assertRaises(
            TypeError, self.export.serialize, args=['json', object]
        )
        self.assertIn(
            type(self.export.serialize('json', queryset=[])), string_types
        )
        object_list = json.loads(
            self.export.serialize('json', queryset=[self.obj])
        )
        self.assertEqual(object_list[0]['fields']['field1'], self.obj.field1)
        self.assertEqual(object_list[0]['fields']['field2'], self.obj.field2)

        # ensure fields are honored
        object_list = json.loads(
            self.export.serialize(
                'json', queryset=[self.obj], fields=['field1']
            )
        )
        self.assertEqual(object_list[0]['fields']['field1'], self.obj.field1)
        self.assertNotIn('field2', object_list[0]['fields'])

    def test_serialize_formats(self):
        for format in ['csv', 'json', 'python', 'xml']:
            self.assertTrue(self.export.serialize(format, queryset=[self.obj]))

    def test_gen_filename(self):
        self.assertEqual(
            self.export.gen_filename('json'),
            "export-export-mockdjangoobject.json"
        )

    def tearDown(self):
        pass


class ExportFlowTestCase(TestCase):
    """
    Testcase for the export tool workflow on the Django User Model
    """

    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser("super", "super@user.com", "super007")
        User.objects.create_user("another", "another@user.com", "another007")
        cls.export_url = "/object-tools/auth/user/export/"

    def setUp(self):
        self.client.login(username="super", password="super007")

    def test_export_xml(self):
        response = self.client.get(path="/admin/auth/user/")
        self.assertEquals(response.status_code, 200)
        response = self.client.get(self.export_url)
        self.assertEquals(response.status_code, 200)
        export_form_data_asc = {
            "export_format": "xml",
            "export_order_by": "username",
            "export_order_direction": "asc"
        }
        export_form_data_dsc = {
            "export_format": "xml",
            "export_order_by": "username",
            "export_order_direction": "dsc"
        }
        response_asc = self.client.post(
            path=self.export_url,
            data=export_form_data_asc,
            follow=True
        )
        response_dsc = self.client.post(
            path=self.export_url,
            data=export_form_data_dsc,
            follow=True
        )
        content_type = response_asc["content-type"]
        self.assertEquals(content_type, "application/xml")
        self.assertNotEqual(response_asc, response_dsc)

    def test_export_json(self):
        export_form_data_jsn = {
            "export_format": "json",
            "export_order_by": "username",
            "export_order_direction": "asc"
        }
        response = self.client.post(
            path=self.export_url,
            data=export_form_data_jsn,
            follow=True
        )
        content_type = response["content-type"]
        self.assertEquals(content_type, "application/json")
        json_content = json.loads(response.content.decode("utf-8"))
        objects = User.objects.count()
        self.assertEquals(type(json_content[0]), dict)
        self.assertEquals(json_content[0]["model"], "auth.user")
        self.assertEquals(objects, len(json_content))

    def test_export_csv(self):
        User.objects.create_user(
            username="FALSE",
            email="someuser@user.com",
            password="another007",
            first_name="[test user]",
            last_name="NULL"
        )
        export_form_data_csv = {
            "export_format": "csv",
            "export_order_by": "username",
            "export_order_direction": "asc"
        }
        response = self.client.post(
            path=self.export_url,
            data=export_form_data_csv,
            follow=True
        )
        content_type = response["content-type"]
        csv_header = '"pk","model","password","last_login","is_superuser","username","first_name","last_name","email","is_staff","is_active","date_joined","groups","user_permissions"'
        test_user = '"NULL","FALSE","\'FALSE\'","\'[test user]\'","\'NULL\'","someuser@user.com","FALSE","TRUE"'
        another_user = '"NULL","FALSE","another","","","another@user.com","FALSE","TRUE"'
        self.assertEquals(content_type, "text/csv")
        self.assertContains(response, csv_header)
        # Check csv serialization rules from csv_serializer.py using
        # the is_superuser, username, first_name, last_name, email,
        # is_staff, is_active columns
        self.assertContains(response, test_user)
        self.assertContains(response, another_user)
