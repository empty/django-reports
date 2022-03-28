from django.conf import settings

JASPER_SERVER = getattr(settings, 'REPORTS_JASPER_SERVER', '')
JASPER_USERNAME = getattr(settings, 'REPORTS_JASPER_USERNAME', '')
JASPER_PASSWORD = getattr(settings, 'REPORTS_JASPER_PASSWORD', '')

REPORTS_LIST = getattr(settings, "REPORTS_REPORTS_LIST", "admin:django_reports_report_changelist")
