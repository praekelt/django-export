import datetime
import time

from django import forms
from django.contrib.admin.widgets import AdminDateWidget, AdminTimeWidget
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import formats        
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

class AdminSplitDateTime(forms.SplitDateTimeWidget):
    """
    A SplitDateTime Widget that has some admin-specific styling.
    """
    def __init__(self, attrs=None):
        widgets = [AdminDateWidget, AdminTimeWidget, AdminDateWidget, AdminTimeWidget]
        # Note that we're calling MultiWidget, not SplitDateTimeWidget, because
        # we want to define widgets.
        forms.MultiWidget.__init__(self, widgets, attrs)

    def format_output(self, rendered_widgets):
        return mark_safe(u'<p class="datetime">%s %s %s %s</p><p class="datetime">%s %s %s %s</p>' % \
            (_('Start Date:'), rendered_widgets[0], _(' Start Time:'), rendered_widgets[1], _('End Date:'), rendered_widgets[2], _('End Time:'), rendered_widgets[3]))


class BasicTextField(forms.fields.CharField):
    def __init__(self, field, *args, **kwargs):
        super(BasicTextField, self).__init__(
            required = False,
            help_text="Only objects containing the entered text in its '%s' field will be exported. Case is ignored." % field.label.lower(),
            *args, **kwargs
        )
    
    def filter(self, name, value, queryset):
        kwargs = {'%s__icontains' % name: value}
        return queryset.filter(**kwargs)


class BooleanField(forms.fields.ChoiceField):
    def __init__(self, field, *args, **kwargs):
        super(BooleanField, self).__init__(
            required = False,
            help_text="Only objects having its '%s' field set as selected will be exported. Select 'Either' to ignore." % field.label.lower(),
            choices=(
                ("", "Either"),
                (True, "Yes"),
                (False, "No"),
            ),
            *args, 
            **kwargs
        )
    
    def filter(self, name, value, queryset):
        if value in ('False', '0'):
            value = False
        elif value in ('True', '1'):
            value = True
        else:
            value = None
        kwargs = {name: bool(value)}
        return queryset.filter(**kwargs)


class CharField(BasicTextField):
    pass


class DateTimeField(forms.fields.DateTimeField):
    def __init__(self, field, *args, **kwargs):
        super(DateTimeField, self).__init__(
            required = False,
            widget = AdminSplitDateTime,
            help_text="Only objects with a '%s' date within the provided range will be exported." % field.label.lower(),
            *args, **kwargs
        )
    
    def to_python(self, value):
        """
        Validates that the input can be converted to a datetime. Returns a
        Python datetime.datetime object.
        """
        if value in validators.EMPTY_VALUES:
            return None
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)
        if isinstance(value, list):
            # Input comes from a 2 SplitDateTimeWidgets, for example. So, it's four
            # components: start date and time, and end date and time.
            if len(value) != 4:
                raise ValidationError(self.error_messages['invalid'])
            if value[0] in validators.EMPTY_VALUES and value[1] in validators.EMPTY_VALUES and value[2] in validators.EMPTY_VALUES and value[3] in validators.EMPTY_VALUES:
                return None
            start_value = '%s %s' % tuple(value[:2])
            end_value = '%s %s' % tuple(value[2:])
        
        start_datetime = None
        end_datetime = None
        for format in self.input_formats or formats.get_format('DATETIME_INPUT_FORMATS'):
            try:
                start_datetime = datetime.datetime(*time.strptime(start_value, format)[:6])
            except ValueError:
                continue
        
        for format in self.input_formats or formats.get_format('DATETIME_INPUT_FORMATS'):
            try:
                end_datetime = datetime.datetime(*time.strptime(end_value, format)[:6])
            except ValueError:
                continue

        return (start_datetime, end_datetime)
    
    def filter(self, name, value, queryset):
        kwargs = {}
        # Filter start datetime.
        if value[0]:
            kwargs = {'%s__gte' % name: value[0]}
        # Filter end datetime.
        if value[1]:
            kwargs = {'%s__lte' % name: value[1]}
        return queryset.filter(**kwargs)


class EmailField(BasicTextField):
    pass


class IPAddressField(BasicTextField):
    pass


class ModelChoiceField(forms.models.ModelChoiceField):
    def __init__(self, field, queryset, *args, **kwargs):
        super(ModelChoiceField, self).__init__(
            queryset=queryset,
            required = False,
            help_text="Only objects with relationships to the selected %s above will be exported. Hold down 'Control', or 'Command' on a Mac, to select more than one." % field.label.lower(),
            *args, **kwargs
        )
    def filter(self, name, value, queryset):
        kwargs = {name: value}
        return queryset.filter(**kwargs)


class ModelMultipleChoiceField(forms.models.ModelMultipleChoiceField):
    def __init__(self, field, queryset, *args, **kwargs):
        super(ModelMultipleChoiceField, self).__init__(
            queryset=queryset,
            required = False,
            help_text="Only objects with relationships to the selected %s above will be exported. Hold down 'Control', or 'Command' on a Mac, to select more than one." % field.label.lower(),
            *args, **kwargs
        )
    def filter(self, name, value, queryset):
        kwargs = {'%s__in' % name: value}
        return queryset.filter(**kwargs)


class URLField(BasicTextField):
    pass
