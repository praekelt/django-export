import json
import inspect
import unittest

from django.db import models

from export import tools


class MockDjangoObject(models.Model):
    field1 = models.IntegerField()
    field2 = models.IntegerField()


class MockDjangoQuerySet(models.QuerySet):
    pass


class FieldsTestCase(unittest.TestCase):
    def test_field_types(self):
        from django.db import models
        from export import fields

        # Very likely need to look into adding support for these field types
        skip_fields = [
            getattr(models.fields.related, 'ForeignObject', None),
            getattr(models.fields, 'GenericIPAddressField', None),
            getattr(models.fields.proxy, 'OrderWrt', None),
            getattr(models.fields, 'BinaryField', None),
            getattr(models.fields, 'FilePathField', None)
        ]

        for key, value in models.__dict__.iteritems():
            try:
                bases = inspect.getmro(value)
            except AttributeError:
                continue

            if models.fields.Field in bases and value not in skip_fields:
                assert getattr(fields, key)


class ToolsTestCase(unittest.TestCase):
    """
    Testcase for tools.Export.
    """
    def setUp(self):
        self.export = tools.Export(MockDjangoObject)
        self.obj = MockDjangoObject(field1=1, field2=2)

    def test_serialize(self):
        self.assertRaises(TypeError, self.export.serialize, args=[object])
        self.assertIsInstance(
            self.export.serialize('json', queryset=[]), unicode
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

    def test_gen_filename(self):
        self.assertEqual(
            self.export.gen_filename('json'),
            "export-export-mockdjangoobject.json"
        )

    def tearDown(self):
        pass
