from django import forms
from django.core import serializers

from export import fields

class Export(forms.Form):
    export_format = forms.ChoiceField(
        choices=[(format, format) for format in serializers.get_serializer_formats()],
        required=False,
        help_text='Designates export format.',
    )

    def __init__(self, model, *args, **kwargs):
        super(Export, self).__init__(*args, **kwargs)
        self.fieldsets = (('Options', {'fields': ('export_format', )}), ('Filters', {'description': 'Objects will be filtered to match the criteria as specified in the fields below. If a value is not specified for a field the field is ignored during the filter process.', 'fields': []}))
        for name, field in forms.models.fields_for_model(model).iteritems():
            if field.__class__ in [forms.models.ModelChoiceField, forms.models.ModelMultipleChoiceField]:
                self.fields[name] = getattr(fields, field.__class__.__name__)(field, field.queryset)
            else:
                self.fields[name] = getattr(fields, field.__class__.__name__)(field)

            if name not in self.fieldsets[1][1]['fields']:
                self.fieldsets[1][1]['fields'].append(name)
