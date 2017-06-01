import mimetypes

from django import template
from django.conf import settings

from django.contrib import messages
from django.contrib.admin import helpers
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext as _

import object_tools
from export import forms, tasks, utils


class Export(object_tools.ObjectTool):
    name = 'export'
    label = 'Export'
    help_text = 'Export filtered objects for download.'
    form_class = forms.Export

    def serialize(self, format, queryset, fields=[]):
        return utils.serialize(format, queryset, fields)

    def gen_filename(self, format):
        app_label = self.model._meta.app_label
        object_name = self.model._meta.object_name.lower()
        if format == 'python':
            format = 'py'
        return '%s-%s-%s.%s' % (self.name, app_label, object_name, format)

    def order(self, queryset, by, direction):
        return utils.order_queryset(queryset, by, direction)

    def has_celery(self):
        return 'djcelery' in getattr(settings, 'INSTALLED_APPS', [])

    def get_queryset(self, form):
        return utils.get_queryset(form, self.model)

    def get_data(self, form):
        queryset = self.get_queryset(form)
        format = form.cleaned_data['export_format']
        fields = form.cleaned_data['export_fields']
        data = self.serialize(format, queryset, fields)

        return format, data

    def export_response(self, form):
        format, data = self.get_data(form)
        filename = self.gen_filename(format)
        response = HttpResponse(
            data, content_type=mimetypes.guess_type(filename)[0]
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response

    def mail_response(self, request, extra_context=None):
        form = extra_context['form']
        format = form.cleaned_data['export_format']
        filename = self.gen_filename(format)

        serializer_kwargs = {
            'fields': form.cleaned_data['export_fields'],
            'format': format
        }

        query_kwargs = {
            'form': form,
            'model': self.model
        }

        # if celery is available send the task, else run as normal
        if self.has_celery():
            return tasks.mail_export.delay(
                request.user.email, filename, serializer_kwargs, query_kwargs
            )
        return utils.mail_export(
            request.user.email, filename, serializer_kwargs, query_kwargs
        )

    def view(self, request, extra_context=None, process_form=True):
        form = extra_context['form']
        if form.is_valid() and process_form:
            if '_export_mail' in request.POST:
                message = _('The export has been generated and will be emailed \
                            to %s.' % (request.user.email))
                messages.add_message(request, messages.SUCCESS, message)
                self.mail_response(request, extra_context)
            else:
                return self.export_response(form)

        adminform = helpers.AdminForm(form, form.fieldsets, {})

        context = {'adminform': adminform}
        context.update(extra_context or {})

        return render(
            request,
            'export/export_form.html',
            context,
        )

object_tools.tools.register(Export)
