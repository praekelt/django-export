import datetime
import time
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.admin.widgets import AdminDateWidget, \
    AdminIntegerFieldWidget, AdminTimeWidget
from django.core import exceptions, validators
from django.core.exceptions import ValidationError
from django.utils import formats
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _


class AdminSplitDateTime(forms.SplitDateTimeWidget):
    """
    A SplitDateTime Widget that has some admin-specific styling.
    """
    def __init__(self, attrs=None):
        widgets = [
            AdminDateWidget, AdminTimeWidget, AdminDateWidget, AdminTimeWidget
        ]
        forms.MultiWidget.__init__(self, widgets, attrs)

    def format_output(self, rendered_widgets):
        return mark_safe(u'<p class="datetime">%s %s %s %s</p>\
                         <p class="datetime">%s %s %s %s</p>' % (
            _('Start Date:'), rendered_widgets[0],
            _(' Start Time:'), rendered_widgets[1],
            _('End Date:'), rendered_widgets[2],
            _('End Time:'), rendered_widgets[3]
        ))


class AdminSplitDate(forms.SplitDateTimeWidget):
    """
    A SplitDate Widget that has some admin-specific styling.
    """
    def __init__(self, attrs=None):
        widgets = [AdminDateWidget, AdminDateWidget]
        forms.MultiWidget.__init__(self, widgets, attrs)

    def format_output(self, rendered_widgets):
        return mark_safe(u'<p class="datetime">%s %s %s %s</p>' % (
            _('Start Date:'), rendered_widgets[0],
            _('End Date:'), rendered_widgets[1])
        )


class AdminSplitTime(forms.SplitDateTimeWidget):
    """
    A SplitDate Widget that has some admin-specific styling.
    """
    def __init__(self, attrs=None):
        widgets = [AdminTimeWidget, AdminTimeWidget]
        forms.MultiWidget.__init__(self, widgets, attrs)

    def format_output(self, rendered_widgets):
        return mark_safe(u'<p class="datetime">%s %s %s %s</p>' % (
            _('Start Time:'), rendered_widgets[0],
            _('End Time:'), rendered_widgets[1])
        )


class AdminSplitInteger(forms.SplitDateTimeWidget):
    """
    A SplitInteger Widget that has some admin-specific styling.
    """
    def __init__(self, attrs=None):
        widgets = [AdminIntegerFieldWidget, AdminIntegerFieldWidget]
        forms.MultiWidget.__init__(self, widgets, attrs)

    def format_output(self, rendered_widgets):
        return mark_safe(u'<p class="datetime">%s %s %s %s</p>' % (
            _('Min:'), rendered_widgets[0], _('Max:'), rendered_widgets[1]
        ))


class BasicTextField(forms.fields.CharField):
    def __init__(self, field, *args, **kwargs):
        super(BasicTextField, self).__init__(
            required=False,
            help_text="Only objects containing the entered text in its '%s' \
                      field will be exported. Case is ignored." % (
            field.label.lower()),
            *args, **kwargs
        )

    def filter(self, name, value, queryset):
        kwargs = {'%s__icontains' % name: value}
        return queryset.filter(**kwargs)


class BooleanField(forms.fields.ChoiceField):
    def __init__(self, field, *args, **kwargs):
        super(BooleanField, self).__init__(
            required=False,
            help_text="Only objects having its '%s' field set as selected will\
                    be exported. Select 'Either' to ignore." % (
            field.label.lower()),
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


class NullBooleanField(BooleanField):
    pass


class CharField(BasicTextField):
    pass


class CommaSeparatedIntegerField(BasicTextField):
    pass


class DateField(forms.fields.DateField):
    def __init__(self, field, *args, **kwargs):
        super(DateField, self).__init__(
            required=False,
            widget=AdminSplitDate,
            help_text="Only objects with a '%s' date within the provided range\
                    will be exported." % field.label.lower(),
            *args, **kwargs
        )

    def to_python(self, value):
        """
        Validates that the input can be converted to a date. Returns a
        Python datetime.date object.
        """
        if value in validators.EMPTY_VALUES:
            return None
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, list):
            # Input comes from a 2 SplitDateWidgets, for example. So, it's two
            # components: start date and end date.
            if len(value) != 2:
                raise ValidationError(self.error_messages['invalid'])
            if value[0] in validators.EMPTY_VALUES and value[1] in \
                    validators.EMPTY_VALUES:
                return None

            start_value = value[0]
            end_value = value[1]

        start_date = None
        end_date = None

        for format in self.input_formats or \
                formats.get_format('DATE_INPUT_FORMATS'):
            try:
                start_date = datetime.datetime(*time.strptime(start_value, \
                        format)[:6]).date()
            except ValueError:
                continue

        for format in self.input_formats or formats.get_format(\
                'DATE_INPUT_FORMATS'):
            try:
                end_date = datetime.datetime(
                    *time.strptime(end_value, format)[:6]
                ).date()
            except ValueError:
                continue

        return (start_date, end_date)

    def filter(self, name, value, queryset):
        kwargs = {}
        # Filter start date.
        if value[0]:
            kwargs['%s__gte' % name] = value[0]
        # Filter end date.
        if value[1]:
            kwargs['%s__lte' % name] = value[1]
        return queryset.filter(**kwargs)


class DateTimeField(forms.fields.DateTimeField):
    def __init__(self, field, *args, **kwargs):
        super(DateTimeField, self).__init__(
            required=False,
            widget=AdminSplitDateTime,
            help_text="Only objects with a '%s' date within the provided \
                    range will be exported." % field.label.lower(),
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
            # Input comes from a 2 SplitDateTimeWidgets, for example. So,
            # it's four components: start date and time, and end date and time.
            if len(value) != 4:
                raise ValidationError(self.error_messages['invalid'])
            if value[0] in validators.EMPTY_VALUES and value[1] in \
                    validators.EMPTY_VALUES and value[2] in \
                    validators.EMPTY_VALUES and value[3] in \
                    validators.EMPTY_VALUES:
                return None
            start_value = '%s %s' % tuple(value[:2])
            end_value = '%s %s' % tuple(value[2:])

        start_datetime = None
        end_datetime = None
        for format in self.input_formats or formats.get_format(\
                'DATETIME_INPUT_FORMATS'):
            try:
                start_datetime = datetime.datetime(*time.strptime(\
                        start_value, format)[:6])
            except ValueError:
                continue

        for format in self.input_formats or formats.get_format(\
                'DATETIME_INPUT_FORMATS'):
            try:
                end_datetime = datetime.datetime(*time.strptime(\
                        end_value, format)[:6])
            except ValueError:
                continue

        return (start_datetime, end_datetime)

    def filter(self, name, value, queryset):
        kwargs = {}
        # Filter start datetime.
        if value[0]:
            kwargs['%s__gte' % name] = value[0]
        # Filter end datetime.
        if value[1]:
            kwargs['%s__lte' % name] = value[1]
        return queryset.filter(**kwargs)


class Field(forms.fields.Field):
    def __init__(self, field, *args, **kwargs):
        super(Field, self).__init__(
            required=False,
            *args, **kwargs
        )


class FileField(BasicTextField):
    pass


class FilePathField(BasicTextField):
    pass


class IntegerField(forms.fields.IntegerField):
    def __init__(self, field, *args, **kwargs):
        super(IntegerField, self).__init__(
            required=False,
            widget=AdminSplitInteger,
            help_text="Only objects with a '%s' value within the provided \
                    range will be exported." % field.label.lower(),
            *args, **kwargs
        )

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        if isinstance(value, list):
            if len(value) != 2:
                raise ValidationError(self.error_messages['invalid'])
            if value[0] in validators.EMPTY_VALUES and value[1] in \
                    validators.EMPTY_VALUES:
                return None

        min = None
        max = None
        if value[0] not in validators.EMPTY_VALUES:
            try:
                min = int(value[0])
            except (TypeError, ValueError):
                raise exceptions.ValidationError(self.error_messages['invalid'])
        if value[1] not in validators.EMPTY_VALUES:
            try:
                max = int(value[1])
            except (TypeError, ValueError):
                raise exceptions.ValidationError(self.error_messages['invalid'])

        return (min, max)

    def filter(self, name, value, queryset):
        kwargs = {}
        # Filter min.
        if value[0]:
            kwargs['%s__gte' % name] = value[0]
        # Filter max.
        if value[1]:
            kwargs['%s__lte' % name] = value[1]
        return queryset.filter(**kwargs)


class FloatField(forms.fields.FloatField):
    def __init__(self, field, *args, **kwargs):
        super(FloatField, self).__init__(
            required=False,
            widget=AdminSplitInteger,
            help_text="Only objects with a '%s' value within the provided \
                    range will be exported." % field.label.lower(),
            *args, **kwargs
        )

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        if isinstance(value, list):
            if len(value) != 2:
                raise ValidationError(self.error_messages['invalid'])
            if value[0] in validators.EMPTY_VALUES and value[1] in \
                    validators.EMPTY_VALUES:
                return None

        min = None
        max = None
        if value[0] not in validators.EMPTY_VALUES:
            try:
                min = float(value[0])
            except (TypeError, ValueError):
                raise exceptions.ValidationError(self.error_messages['invalid'])
        if value[1] not in validators.EMPTY_VALUES:
            try:
                max = float(value[1])
            except (TypeError, ValueError):
                raise exceptions.ValidationError(self.error_messages['invalid'])

        return min, max

    def filter(self, name, value, queryset):
        kwargs = {}
        # Filter min.
        if value[0]:
            kwargs['%s__gte' % name] = value[0]
        # Filter max.
        if value[1]:
            kwargs['%s__lte' % name] = value[1]
        return queryset.filter(**kwargs)


class ImageField(BasicTextField):
    pass


class DecimalField(forms.fields.DecimalField):
    def __init__(self, field, *args, **kwargs):
        super(DecimalField, self).__init__(
            required=False,
            widget=AdminSplitInteger,
            help_text="Only objects with a '%s' value within the provided \
                    range will be exported." % field.label.lower(),
            *args, **kwargs
        )

    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        if isinstance(value, list):
            if len(value) != 2:
                raise ValidationError(self.error_messages['invalid'])
            if value[0] in validators.EMPTY_VALUES and value[1] in \
                    validators.EMPTY_VALUES:
                return None

        min = None
        max = None
        if value[0] not in validators.EMPTY_VALUES:
            try:
                min = Decimal(value[0])
            except (TypeError, ValueError, InvalidOperation):
                raise exceptions.ValidationError(self.error_messages['invalid'])
        if value[1] not in validators.EMPTY_VALUES:
            try:
                max = Decimal(value[1])
            except (TypeError, ValueError, InvalidOperation):
                raise exceptions.ValidationError(self.error_messages['invalid'])

        return min, max

    def validate(self, value):
        if value in validators.EMPTY_VALUES:
            return
        return (super(DecimalField, self).validate(value[0]), \
                super(DecimalField, self).validate(value[1]))

    def filter(self, name, value, queryset):
        kwargs = {}
        # Filter min.
        if value[0]:
            kwargs['%s__gte' % name] = value[0]
        # Filter max.
        if value[1]:
            kwargs['%s__lte' % name] = value[1]
        return queryset.filter(**kwargs)


class AutoField(IntegerField):
    pass


class BigAutoField(IntegerField):
    pass


class BigIntegerField(IntegerField):
    pass


class PositiveIntegerField(IntegerField):
    pass


class PositiveSmallIntegerField(IntegerField):
    pass


class SmallIntegerField(IntegerField):
    pass


class EmailField(BasicTextField):
    pass


class IPAddressField(BasicTextField):
    pass


class ModelMultipleChoiceField(forms.models.ModelMultipleChoiceField):
    def __init__(self, field, queryset, *args, **kwargs):
        super(ModelMultipleChoiceField, self).__init__(
            queryset=queryset,
            required=False,
            help_text="Only objects with relationships to the selected %s \
                    above will be exported. Hold down 'Control', or 'Command' \
                    on a Mac, to select more than one." % field.label.lower(),
            *args, **kwargs
        )

    def filter(self, name, value, queryset):
        kwargs = {'%s__in' % name: value}
        return queryset.filter(**kwargs)


class ModelChoiceField(ModelMultipleChoiceField):
    pass


class OneToOneField(ModelMultipleChoiceField):
    pass


class ForeignKey(ModelMultipleChoiceField):
    pass


class ManyToManyField(ModelMultipleChoiceField):
    pass


class TextField(BasicTextField):
    pass


class TimeField(forms.fields.TimeField):
    def __init__(self, field, *args, **kwargs):
        super(TimeField, self).__init__(
            required=False,
            widget=AdminSplitTime,
            help_text="Only objects with a '%s' time within the provided range\
                    will be exported." % field.label.lower(),
            *args, **kwargs
        )

    def to_python(self, value):
        """
        Validates that the input can be converted to a time. Returns a
        Python datetime.time object.
        """
        if value in validators.EMPTY_VALUES:
            return None
        if isinstance(value, datetime.datetime):
            return value.time()
        if isinstance(value, datetime.time):
            return value
        if isinstance(value, list):
            # Input comes from a 2 SplitTimeWidgets, for example. So, it's two
            # components: start time and end time.
            if len(value) != 2:
                raise ValidationError(self.error_messages['invalid'])
            if value[0] in validators.EMPTY_VALUES and value[1] in \
                    validators.EMPTY_VALUES:
                return None

            start_value = value[0]
            end_value = value[1]

        start_time = None
        end_time = None

        for format in self.input_formats or formats.get_format(\
                'TIME_INPUT_FORMATS'):
            try:
                start_time = datetime.datetime(
                    *time.strptime(start_value, format)[:6]
                ).time()
            except ValueError:
                if start_time:
                    continue
                else:
                    raise ValidationError(self.error_messages['invalid'])

        for format in self.input_formats or formats.get_format(\
                'TIME_INPUT_FORMATS'):
            try:
                end_time = datetime.datetime(
                    *time.strptime(end_value, format)[:6]
                ).time()
            except ValueError:
                if end_time:
                    continue
                else:
                    raise ValidationError(self.error_messages['invalid'])

        return (start_time, end_time)

    def filter(self, name, value, queryset):
        kwargs = {}
        # Filter start date.
        if value[0]:
            kwargs['%s__gte' % name] = value[0]
        # Filter end date.
        if value[1]:
            kwargs['%s__lte' % name] = value[1]

        return queryset.filter(**kwargs)


class SlugField(BasicTextField):
    pass


class URLField(BasicTextField):
    pass


class XMLField(BasicTextField):
    pass
