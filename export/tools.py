import mimetypes

from django import template
from django.conf import settings
from django.core import serializers
from django.contrib import messages
from django.contrib.admin import helpers
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _

import object_tools
from export import forms, tasks, utils


class Export(object_tools.ObjectTool):
    name = 'export'
    label = 'Export'
    help_text = 'Export filtered objects for download.'
    form_class = forms.Export

    def serialize(self, format, queryset, fields=[]):
        serializer = serializers.get_serializer(format)()
        if fields:
            return serializer.serialize(queryset, fields=fields, indent=4)
        else:
            return serializer.serialize(queryset, indent=4)

    def gen_filename(self, format):
        app_label = self.model._meta.app_label
        object_name = self.model._meta.object_name.lower()
        if format == 'python':
            format = 'py'
        return '%s-%s-%s.%s' % (self.name, app_label, object_name, format)

    def order(self, queryset, by, direction):
        if direction == 'dsc':
            order_str = '-%s' % by
        else:
            order_str = by
        return queryset.order_by(order_str)

    def has_celery(self):
        return 'djcelery' in getattr(settings, 'INSTALLED_APPS', [])

    def get_data(self, form):
        queryset = self.model.objects.all()
        for name, value in form.cleaned_data.iteritems():
            if name not in form.fieldsets[0][1]['fields']:
                if value:
                    queryset = form.fields[name].filter(name, value, queryset)

        order_by = form.cleaned_data['export_order_by']
        order_direction = form.cleaned_data['export_order_direction']
        queryset = self.order(queryset, order_by, order_direction)

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
        format, data = self.get_data(form)
        filename = self.gen_filename('zip')

        # if celery is available send the task, else run as normal
        if self.has_celery():
            return tasks.mail_export.delay(request.user.email, filename, data)
        return utils.mail_export(request.user.email, filename, data)

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
        context_instance = template.RequestContext(request)

        return render_to_response(
            'export/export_form.html',
            context,
            context_instance=context_instance
        )

object_tools.tools.register(Export)
