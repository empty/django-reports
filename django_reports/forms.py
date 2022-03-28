
import datetime

from django import forms

from .widgets import DateInput


class ReportForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(ReportForm, self).__init__(*args, **kwargs)


class SinceDateForm(ReportForm):
    start_date = forms.DateField(
        label="Since",
        initial=lambda: (datetime.date.today() - datetime.timedelta(days=90))
    )


class BetweenDateForm(ReportForm):
    start_date = forms.DateField(
        label="From",
        initial=lambda: (datetime.date.today() - datetime.timedelta(days=30)),
        widget=DateInput,
    )
    end_date = forms.DateField(label="To", initial=datetime.date.today, widget=DateInput)
