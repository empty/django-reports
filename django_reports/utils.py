
import datetime
import decimal

from collections import OrderedDict
from importlib import import_module

from django.conf import settings
from django.db import connection
from django.db.models.query import QuerySet
from django.http import HttpResponse


def get_form(report):
    form_name = report.form.split('.')
    module = import_module('.'.join(form_name[:-1]))
    klass = form_name[-1]
    return module, klass


def get_view(report):
    view_name = report.view.split('.')
    module = import_module('.'.join(view_name[:-1]))
    klass = view_name[-1]
    return module, klass


def get_fieldsets(form):
    return [(None, {'fields': list(form.base_fields)})]


class ExcelResponse(HttpResponse):
    def __init__(self, data, output_name='excel_data', headers=None,
                 force_csv=False, encoding='utf8', percentage_formats=[]):

        valid_data = False
        if isinstance(data, QuerySet):
            data = list(data.values())
        if hasattr(data, '__getitem__'):
            if isinstance(data[0], dict):
                if headers is None:
                    headers = list(data[0].keys())
                data = [[row[col] for col in headers] for row in data]
                data.insert(0, headers)
            if hasattr(data[0], '__getitem__'):
                if headers is not None:
                    data.insert(0, headers)
                valid_data = True
        assert valid_data is True, "ExcelResponse requires a sequence of sequences"

        import io
        output = io.BytesIO()
        # Excel has a limit on number of rows; if we have more than that, make a csv
        use_xls = False
        if len(data) <= 65536 and force_csv is not True:
            try:
                import xlwt
                use_xls = True
            except ImportError:
                # xlwt doesn't exist; fall back to csv
                pass
        if use_xls:
            book = xlwt.Workbook(encoding=encoding)
            sheet = book.add_sheet('Sheet 1')
            styles = {'datetime': xlwt.easyxf(num_format_str='yyyy-mm-dd hh:mm:ss'),
                      'date': xlwt.easyxf(num_format_str='yyyy-mm-dd'),
                      'time': xlwt.easyxf(num_format_str='hh:mm:ss'),
                      'percentage': xlwt.easyxf(num_format_str='0%'),
                      'percentage1': xlwt.easyxf(num_format_str='0.0%'),
                      'percentage2': xlwt.easyxf(num_format_str='0.00%'),
                      'default': xlwt.Style.default_style}

            for rowx, row in enumerate(data):
                for colx, value in enumerate(row):
                    if isinstance(value, datetime.datetime):
                        cell_style = styles['datetime']
                    elif isinstance(value, datetime.date):
                        cell_style = styles['date']
                    elif isinstance(value, datetime.time):
                        cell_style = styles['time']
                    elif self.is_percentage(value):
                        value = decimal.Decimal(value.replace('%', '')) / 100
                        cell_style = self.get_percentage_style(rowx - 1, percentage_formats, styles)
                    else:
                        cell_style = styles['default']
                    if rowx == 0:
                        header_style = xlwt.Style.XFStyle()
                        header_style.font.bold = True
                        sheet.write(rowx, colx, value, style=header_style)
                    else:
                        sheet.write(rowx, colx, value, style=cell_style)

            book.save(output)
            mimetype = 'application/vnd.ms-excel'
            file_ext = 'xls'
        else:
            for row in data:
                out_row = []
                for value in row:
                    if not isinstance(value, str):
                        value = str(value)
                    out_row.append(value.replace('"', '""'))
                csv_row = '"{0}"\n'.format('","'.join(out_row))
                output.write(csv_row.encode(encoding))
            mimetype = 'text/csv'
            file_ext = 'csv'
        output.seek(0)
        super(ExcelResponse, self).__init__(content=output.getvalue(),
                                            content_type=mimetype)
        self['Content-Disposition'] = 'attachment;filename="%s.%s"' % \
            (output_name.replace('"', '\"'), file_ext)

    def is_percentage(self, string):
        if isinstance(string, str) and '%' in string:
            return self.is_number(string.replace('%', ''))
        return False

    def is_number(self, string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    def get_percentage_style(self, index, formats, styles):
        if formats and index < len(formats) and formats[index]:
            return styles[formats[index]]
        return styles['default']


class NoResultsException(Exception):
    pass


class InvalidJasperReportException(Exception):
    pass


def generate_report(request, report, format, output_name, parameters, split_parameters):
    # view driven report
    if report.view:
        module, klass = get_view(report)
        kwargs = OrderedDict(zip(split_parameters, parameters))
        kwargs['format'] = format
        return getattr(module, klass)(request, **kwargs)

    # jasper driven report
    if report.url:
        from . import python_jasper
        server = python_jasper.JasperServer("http://%s/jasperserver/rest_v2/reports" % settings.JASPER_SERVER, settings.JASPER_USERNAME, settings.JASPER_PASSWORD)
        response = server.run_report(report.url, request.GET.urlencode())

        if response.status_code != 200:
            raise InvalidJasperReportException("The report configuration is invalid.")

        final_response = HttpResponse(response.content, content_type='application/pdf')
        final_response['Content-Disposition'] = 'attachment; filename=%s.pdf' % output_name
        return final_response

    # sql driven report
    if report.sql:
        cursor = connection.cursor()
        if parameters:
            cursor.execute(report.sql, tuple(parameters))
        else:
            cursor.execute(report.sql)

        headers = [h[0] for h in cursor.description]
        data = cursor.fetchall()
        if data:
            return ExcelResponse(data, output_name=output_name, headers=headers, force_csv=(format == 'csv'))
        raise NoResultsException("%s did not return any results." % report.name)


def format_as_joda(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S')
