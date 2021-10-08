from datetime import timezone

import aniso8601
import arrow
from django import forms
from datetime import timedelta


class ArrowDurationFieldForm(forms.DurationField):

    def prepare_value(self, value):
        if isinstance(value, timedelta):
            return value.total_seconds()
        return super().to_python(value)

    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, timedelta):
            return value
        elif isinstance(value, float):
            return timedelta(seconds=value)
        return super().to_python(value)
