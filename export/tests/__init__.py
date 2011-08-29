import inspect
import unittest


class FieldsTestCase(unittest.TestCase):
    def test_field_types(self):
        from django.db import models
        from export import fields

        for key, value in models.__dict__.iteritems():
            try:
                bases = inspect.getmro(value)
            except AttributeError:
                bases = None
            if bases:
                if models.fields.Field in bases and value != \
                        models.fields.Field:
                    getattr(fields, key)
