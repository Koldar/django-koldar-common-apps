from datetime import timezone

import arrow
from django import forms


class ArrowFieldForm(forms.DateTimeField):
    input_formats = {
        'YYYY-MM-DD HH:mm:ss',
        'YYYY-MM-DD HH:mm',
        'YYYY-MM-DD',
        'DD/MM/YYYY HH:mm:ss',
        'DD/MM/YYYY HH:mm',
        'DD/MM/YYYY',
    }

    def prepare_value(self, value):
        if isinstance(value, arrow.Arrow):
            return value.naive
        return super().to_python(value)

    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, arrow.Arrow):
            value.to(timezone.utc)
            return value
        return super().to_python(value)

    def strptime(self, value, format):
        return arrow.get(value, format, tzinfo=timezone.utc)
