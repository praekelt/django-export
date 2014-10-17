from export.utils import mail_export

try:
    from celery import task
    mail_export = task(mail_export)
except ImportError:
    pass
