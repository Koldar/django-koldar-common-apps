import abc
from typing import Dict, List, Tuple, Optional, TypeVar, Generic, Union

from django.db import models

TFIELD = TypeVar("TFIELD")
"""
python type that this fields stores.
"""


class AbstractDjangoField(models.Field, Generic[TFIELD], abc.ABC):
    """
    Ab abstract class used to document what are the method you need to overwrite
    ion order to have a compliant field implementation
    """

    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abc.abstractmethod
    def deconstruct(self) -> Tuple[str, str, List[any], Dict[str, any]]:
        """
        Reverse operation of __init__: given an instance, generates the parameters required to run init.

        Remember:
        for any configuration of your Field instance, deconstruct() must return arguments that
        you can pass to __init__ to reconstruct that state.

        If you haven’t added any extra options on top of the field you inherited from,
        then there’s no need to write a new deconstruct() method. If, however, you’re changing the arguments passed
        in __init__() (like we are in HandField), you’ll need to supplement the values being passed.

        .. ::code-block::
            def deconstruct(self) -> Tuple[str, str, List[any], Dict[str, any]]:
                return super().deconstruct()

        If you add a new keyword in the __init__, you need to fetch it from "self" instance and add it to kwargs:

        .. ::code-block::
            def deconstruct(self) -> Tuple[str, str, List[any], Dict[str, any]]:
                name, full_path, args, kwargs = super().deconstruct()
                kwargs["new_keyword"] = self.new_keyword
                return name, full_path, args, kwargs


        :return: tuple of 4 elements:
            - the field’s attribute name,
            - the full import path of the field class,
            - the positional arguments (as a list),
            - and the keyword arguments (as a dict);

        """
        pass

    @abc.abstractmethod
    def db_type(self, connection) -> Optional[any]:
        return super().db_type(connection)

    @abc.abstractmethod
    def to_python(self, value: Optional[Union[TFIELD, any, str]]) -> Optional[TFIELD]:
        """
        Convert a generic value into a value that is storeed in this field type.
        This method is called whenever we need to store
        As a general rule, to_python() should deal gracefully with any of the following arguments:

         - An instance of the correct type (e.g., Hand in our ongoing example);
         - A string;
         - None (if the field allows null=True);

        """
        return super().to_python(value)

    @abc.abstractmethod
    def from_db_value(self, value: Optional[any], expression, connection) -> Optional[TFIELD]:
        """
        Called when the data **is strictly loaded from the database**, including in aggregates and values() calls.
        If the data is not fetched from the database, the function will **not** be called

        :param value: is the value we fetch from the database (may be None)
        :param expression: expression that generated the value
        :param connection: db connection
        :return: the python value repersented by the specific db value
        """
        pass

    @abc.abstractmethod
    def get_prep_value(self, value: Optional[TFIELD]):
        """
        Convert a python object that is stored in the field into an object that will be stored in the database.
        Concretely, it is the reverse operation of from_db_value: if you have overwritten from_db_value, you
        need to extend this method as well
        """
        return super().get_prep_value(value)

    def get_db_prep_value(self, value: Optional[TFIELD], connection, prepared: bool = False):
        """
        Some data types (for example, dates) need to be in a specific format before they can be used by
        a database backend. get_db_prep_value() is the method where those conversions should be
        made. The specific connection that will be used for the query is passed as the connection parameter.
        This allows you to use backend-specific conversion logic if it is required.
        """
        return super().get_db_prep_value(value, connection, prepared)

    def pre_save(self, model_instance, add):
        """
        If you want to preprocess the value just before saving, you can use pre_save(). For example,
        Django’s DateTimeField uses this method to set the attribute correctly in the case of auto_now or auto_now_add.

        If you do override this method, you must return the value of the attribute at the end. You should also update the
        model’s attribute if you make any changes to the value so that code holding references to the model will always see the correct value

        :param model_instance: model containing the value to save
        :param add: if True, we a re saving the entity for the first time
        :return: It should return the value of the appropriate
        attribute from model_instance for this field. The attribute name is in self.attname (this is set up by Field).
        """
        pass

    @abc.abstractmethod
    def formfield(self, **kwargs):
        """
        To customize the form field used by ModelForm, you can override formfield().

        The form field class can be specified via the form_class and choices_form_class arguments;
        the latter is used if the field has choices specified, the former otherwise. If these arguments are
        not provided, CharField or TypedChoiceField will be used.

        All of the kwargs dictionary is passed directly to the form field’s __init__() method.
        Normally, all you need to do is set up a good default for the form_class (and maybe choices_form_class)
        argument and then delegate further handling to the parent class. This might require you to write a custom
        form field (and even a form widget). See the forms documentation for information about this.

        .. :code-block: python
            def formfield(self, **kwargs):
                defaults = {'form_class': ArrowFieldForm}
                defaults.update(kwargs)
                return super().formfield(**defaults)

        """
        pass


class AbstractDjangoFileField(AbstractDjangoField, abc.ABC):

    @classmethod
    @abc.abstractmethod
    def get_attr_class(cls) -> type:
        """
        The attr class of this file

        :return: something like ImageFieldFile or a type extending AbstractDjangoAttrClass
        """
        pass


class AbstractDjangoAttrClass(abc.ABC):

    @abc.abstractmethod
    def delete(self, save=True):
        pass

    @abc.abstractmethod
    def save(self, name: str, content, save=True, *args, **kwargs):
        pass