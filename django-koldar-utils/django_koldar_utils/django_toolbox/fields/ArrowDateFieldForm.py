from datetime import timezone

import arrow
from django import forms


class ArrowDateFieldForm(forms.DateField):
    input_formats = {
        'YYYY-MM-DD',
        'DD/MM/YYYY',
    }

    def prepare_value(self, value):
        if isinstance(value, arrow.Arrow):
            return value.date()
        return super().to_python(value)

    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, arrow.Arrow):
            return value
        return super().to_python(value)

    def strptime(self, value, format):
        return arrow.get(value, format, tzinfo=timezone.utc)
