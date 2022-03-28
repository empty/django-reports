from django.forms import TextInput


class ColorInput(TextInput):
    input_type = 'color'


class DateInput(TextInput):
    input_type = 'date'
