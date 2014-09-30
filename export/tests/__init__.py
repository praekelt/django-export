import inspect
import unittest


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
