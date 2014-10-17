import StringIO
from zipfile import ZipFile

from django.core import serializers
from django.core.mail import EmailMessage
from django.utils.translation import ugettext as _


def mail_export(email, filename, serializer_kargs):
    data = serialize(**serializer_kargs)

    zip_data = StringIO.StringIO()
    zipfile = ZipFile(zip_data, mode='w')
    zipfile.writestr(str(filename), str(data))
    zipfile.close()

    subject = _("Database Export")
    message = _("Database Export Attached")
    email = EmailMessage(subject, message, to=[email])
    email.attach(filename, zip_data.getvalue(), 'application/zip')
    email.send()

    zip_data.close()


def serialize(format, queryset, fields=[]):
    serializer = serializers.get_serializer(format)()
    if fields:
        return serializer.serialize(queryset, fields=fields, indent=4)
    else:
        return serializer.serialize(queryset, indent=4)
