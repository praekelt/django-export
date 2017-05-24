import json
import six

from django.db import models
from django.test import TestCase

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
        self.assertRaises(
            TypeError, self.export.serialize, args=['json', object]
        )
        if six.PY2:
            self.assertIn(
                type(self.export.serialize('json', queryset=[])), [unicode, str]
            )
        else:
            self.assertIn(
                type(self.export.serialize('json', queryset=[])), [str]
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
