import inspect

from django.db import models
from django.test import TestCase

from export import fields


class FieldsTestCase(TestCase):

    def test_field_types(self):
        # Fields not supported at present
        skip_fields = [
            getattr(models.fields.related, 'ForeignObject', None),
            getattr(models.fields, 'GenericIPAddressField', None),
            getattr(models.fields.proxy, 'OrderWrt', None),
            getattr(models.fields, 'BinaryField', None),
            getattr(models.fields, 'FilePathField', None),
            getattr(models.fields, 'DurationField', None),
            getattr(models.fields, 'UUIDField', None)
        ]

        for key, value in models.__dict__.items():
            try:
                bases = inspect.getmro(value)
            except AttributeError:
                continue

            if models.fields.Field in bases and value not in skip_fields:
                assert getattr(fields, key)
