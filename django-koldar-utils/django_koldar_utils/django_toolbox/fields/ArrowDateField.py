import datetime
from typing import Optional, Union

import arrow
from arrow import Arrow
from django.db import models

from django_koldar_utils.django_toolbox.fields import ArrowDateFieldForm
from django_koldar_utils.django_toolbox.fields.ArrowFieldForm import ArrowFieldForm


class ArrowDateField(models.DateField):

    description = "A value encapsulating a local date using arrow project"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs

    def db_type(self, connection):
        return super().db_type(connection)

    def from_db_value(self, value, expression, connection) -> Optional[arrow.Arrow]:
        """
        Convert sdomething fetched from the database to a python object
        """
        if value is None:
            return None
        if isinstance(value, arrow.Arrow):
            return value
        return arrow.get(value)

    def get_prep_value(self, value: Optional[arrow.Arrow]) -> Optional[datetime.date]:
        """
        Convert a python object into something that can be serialized into the database
        """
        if value:
            return value.date()
        else:
            return None

    def to_python(self, value: Optional[Union[arrow.Arrow, str]]) -> Optional[arrow.Arrow]:
        """
        Convert something fetched from the database to a python object
        """
        if value is None:
            return None
        if isinstance(value, arrow.Arrow):
            return value
        return arrow.get(value)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return '' if value is None else value.isoformat()

    def pre_save(self, model_instance, add):
        """
        If you want to preprocess the value just before saving, you can use pre_save(). For example,
        Django’s DateTimeField uses this method to set the attribute correctly in the case of auto_now or auto_now_add.

        If you do override this method, you must return the value of the attribute at the end. You should also update the
        model’s attribute if you make any changes to the value so that code holding references to the model will always see the correct value
        """
        if self.auto_now or (self.auto_now_add and add):
            value = Arrow.utcnow().date()
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super().pre_save(model_instance, add)

    def formfield(self, **kwargs):
        """
        To customize the form field used by ModelForm, you can override formfield().

        The form field class can be specified via the form_class and choices_form_class arguments;
        the latter is used if the field has choices specified, the former otherwise. If these arguments are
        not provided, CharField or TypedChoiceField will be used.

        All of the kwargs dictionary is passed directly to the form field’s __init__() method.
        Normally, all you need to do is set up a good default for the form_class (and maybe choices_form_class)
        argument and then delegate further handling to the parent class. This might require you to write a custom
        form field (and even a form widget). See the forms documentation for information about this
        """
        defaults = {'form_class': ArrowDateFieldForm}
        defaults.update(kwargs)
        return super().formfield(**defaults)
