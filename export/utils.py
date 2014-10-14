import StringIO
from zipfile import ZipFile

from django.core.mail import EmailMessage
from django.utils.translation import ugettext as _


def mail_export(email, filename, data):
    zip_data = StringIO.StringIO()
    zipfile = ZipFile(unicode(zip_data), mode='w')
    zipfile.writestr(filename, data)
    zipfile.close()

    subject = _("Database Export")
    message = _("Database Export Attached")
    email = EmailMessage(subject, message, to=[email])
    email.attach(filename, zip_data.getvalue(), 'application/zip')
    email.send()

    zipfile.close()
