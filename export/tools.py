import mimetypes
import StringIO
from zipfile import ZipFile

from django import template
from django.core import serializers
from django.core.mail import EmailMessage
from django.contrib.admin import helpers
from django.http import HttpResponse
from django.shortcuts import render_to_response

import object_tools
from export import forms


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
        data, format = self.get_data(form)
        filename = self.gen_filename(format)
        response = HttpResponse(
            data, mimetype=mimetypes.guess_type(filename)[0]
        )
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response

    def mail_response(self, form, request):
        data, format = self.get_data(form)
        filename = self.gen_filename('zip')

        zip_data = StringIO.StringIO()
        zipfile = ZipFile(zip_data, mode='w')
        zipfile.writestr(filename, data)
        zipfile.close()

        subject = "Database Export"
        message = "Database Export Attached"
        email = EmailMessage(subject, message, to=[request.user.email])
        email.attach(filename, zip_data.getvalue(), 'application/zip')
        email.send()

    def view(self, request, extra_context=None):
        form = extra_context['form']
        if form.is_valid():
            if form.cleaned_data['email_export']:
                return self.mail_response(form, request)
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
