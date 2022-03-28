
from django.urls import reverse
from django.db import models
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _


class Category(models.Model):
    name = models.CharField(_('category'), max_length=50)

    class Meta(object):
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Report(models.Model):
    name = models.CharField(_('name'), max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField(_('description'))
    sql = models.TextField(_('sql'), blank=True)
    url = models.CharField(_('url'), max_length=1000, blank=True)
    view = models.CharField(_('view'), max_length=1000, blank=True)
    category = models.ForeignKey(Category, models.CASCADE, null=True, blank=True)
    form = models.CharField(_('form'), max_length=500, blank=True)
    parameters = models.CharField(_('parameters'), max_length=4000, blank=True)

    class Meta(object):
        verbose_name = 'report'
        verbose_name_plural = 'reports'
        ordering = ('name',)

    def __str__(self):
        return self.name

    def report_type(self):
        result = ''
        if self.form:
            result += 'form / '
        if self.view:
            result += 'view'
        elif self.url:
            result += 'jasper'
        elif self.sql:
            result += 'sql'
        return result

    def admin_run_report(self):
        result = ''
        if self.url:
            result = '<a href="%s">PDF</a>' % reverse('admin:reports_report_run', args=[self.pk, 'pdf'])
        else:
            result = '<a href="%s">Excel</a>' % reverse('admin:reports_report_run', args=[self.pk, 'excel'])
            result += ' / <a href="%s">CSV</a>' % reverse('admin:reports_report_run', args=[self.pk, 'csv'])
        return format_html(result)
    admin_run_report.short_description = 'Format'
