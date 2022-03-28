
import datetime

from django.conf.urls import url
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.html import format_html

from django.contrib import admin
from django.contrib import messages

from .conf import settings
from .models import Category, Report
from .utils import get_fieldsets, get_form, generate_report, InvalidJasperReportException, NoResultsException


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ReportAdmin(admin.ModelAdmin):
    list_display = ('admin_run_report', 'name', 'report_type', 'description', 'category', 'admin_edit')
    list_filter = ('category',)
    suit_list_filter_horizontal = ('category',)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ('name', 'description',)

    def get_urls(self):
        urls = super(ReportAdmin, self).get_urls()
        custom_urls = [
            url(r'^run/(?P<id>\d+)/(?P<format>\w+)/$', self.admin_site.admin_view(self.run), name='reports_report_run'),
        ]
        return custom_urls + urls

    def admin_edit(self, obj):
        return format_html("<a href=\"{0}\">Edit</a>".format(
            reverse('admin:reports_report_change', args=(obj.id,))
        ))
    admin_edit.short_description = 'Edit'

    def run(self, request, id, format):
        report = get_object_or_404(Report, pk=id)

        if not report.form or request.method == 'POST':
            now = datetime.datetime.now()
            output_name = "%s_%s_%s" % (report.slug, now.strftime("%Y-%m-%d"), now.microsecond)
            parameters = []
            split_parameters = [p.strip() for p in report.parameters.split(',')]

            if report.form:
                module, klass = get_form(report)
                form = getattr(module, klass)(request.POST, request=request)
                if form.is_valid():
                    for field in split_parameters:
                        parameters.append(request.POST.get(field.strip()))
                else:
                    admin_form = admin.helpers.AdminForm(
                        form,
                        get_fieldsets(form),
                        {},
                        (),
                        model_admin=self)
                    # media = self.media + admin_form.media

                    context = dict(
                        self.admin_site.each_context(request),
                        report=report,
                        adminform=admin_form,
                        format=format,
                        is_popup=False,
                        inline_admin_formsets=[]
                    )
                    return self.render_change_form(request, context, add=True)

            try:
                return generate_report(request, report, format, output_name, parameters, split_parameters)
            except NoResultsException:
                messages.info(request, "%s did not return any results." % report.name)
                return redirect(settings.REPORTS_LIST)
            except InvalidJasperReportException:
                messages.error(request, "The report configuration is invalid.")
                return redirect(settings.REPORTS_LIST)

        module, klass = get_form(report)
        form = getattr(module, klass)(request=request)

        admin_form = admin.helpers.AdminForm(
            form,
            get_fieldsets(form),
            {},
            (),
            model_admin=self)
        # media = self.media + admin_form.media

        context = dict(
            self.admin_site.each_context(request),
            report=report,
            adminform=admin_form,
            format=format,
            is_popup=False,
            inline_admin_formsets=[]
        )
        return self.render_change_form(request, context, add=True)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Report, ReportAdmin)
