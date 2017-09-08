try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import zipfile

from django.core import serializers
from django.core.mail import EmailMessage
from django.utils.translation import ugettext as _


def mail_export(email, filename, serializer_kwargs, query_kwargs):
    queryset = get_queryset(**query_kwargs)
    data = serialize(queryset=queryset, **serializer_kwargs)

    zip_data = StringIO()
    zip_file = zipfile.ZipFile(
        zip_data, mode='w', compression=zipfile.ZIP_DEFLATED
    )
    zip_file.writestr(str(filename), str(data))
    zip_file.close()

    subject = _("Database Export")
    message = _("Database Export Attached")
    email = EmailMessage(subject, message, to=[email])
    email.attach("%s.zip" % filename, zip_data.getvalue(), 'application/zip')
    email.send()

    zip_data.close()


def serialize(format, queryset, fields=[]):
    serializer = serializers.get_serializer(format)()
    if fields:
        return serializer.serialize(queryset, fields=fields, indent=4)
    else:
        return serializer.serialize(queryset, indent=4)


def order_queryset(queryset, by, direction):
    if direction == 'dsc':
        order_str = '-%s' % by
    else:
        order_str = by
    return queryset.order_by(order_str)


def get_queryset(form, model):
    queryset = model.objects.all()
    for name, value in form.cleaned_data.items():
        if name not in form.fieldsets[0][1]['fields']:
            if value:
                queryset = form.fields[name].filter(name, value, queryset)

    order_by = form.cleaned_data['export_order_by']
    order_direction = form.cleaned_data['export_order_direction']

    return order_queryset(queryset, order_by, order_direction)
