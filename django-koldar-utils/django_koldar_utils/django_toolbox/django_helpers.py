import sys
from typing import Iterable, Optional, Union, List

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.apps import apps

DEFAULT_NAMES_TO_CHECK = ["is_active", "active", "deleted"]

def get_active_flag_name_or_none(model: Union[type, models.Model], names_to_check: List[str] = None) -> Optional[str]:
    """
    Trying to fetch the flag representing whether or not the model is active or not

    :param model: either the type of the django model or an instance of it
    :param names_to_check: flag names to check for the specified model
    :return: the name of the flag representing if the model is active or not. If we cannot find it, we return None
    """
    if names_to_check is None:
        names_to_check = DEFAULT_NAMES_TO_CHECK
    if isinstance(model, models.Model):
        model = type(model)

    for x in names_to_check:
        try:
            val = getattr(model, x)
            return x
        except AttributeError:
            continue
    else:
        return None


def is_active_flag(instance: models.Model, default_value: bool = True, names_to_check: List[str] = None) -> bool:
    """
    Check if the active flag is true or false

    :param instance: the isntan ce whose active flag we need to check
    :param names_to_check: flag names to check for the specified model
    :param default_value: the value to return if the instance does not have an active flag
    :return: active flag value
    """

    if names_to_check is None:
        names_to_check = DEFAULT_NAMES_TO_CHECK
    flag_name = get_active_flag_name_or_none(instance, names_to_check)
    if flag_name is None:
        return default_value
    else:
        return bool(getattr(instance, flag_name))


def set_active_flag_to(instance: models.Model, enable: bool, names_to_check: List[str] = None):
    """
    Set the active flag to a specific value.
    if the instance does not have an active flag, we do nothing

    :param instance: instance of the model whose active flag we need to check
    :param names_to_check: flag names to check for the specified model
    :return: true if the flag was present, false otherwise
    """
    if names_to_check is None:
        names_to_check = DEFAULT_NAMES_TO_CHECK
    flag_name = get_active_flag_name_or_none(instance, names_to_check=names_to_check)
    if flag_name is not None:
        setattr(instance, flag_name, enable)
    return flag_name is not None


def get_all_app_names() -> Iterable[str]:
    """
    :return: an iterable specifying all the app verbose names
    """
    for app in apps.get_app_configs():
        yield app.verbose_name


def get_all_app_install_directory() -> Iterable[str]:
    """
    :return: an iterable specifying all the isntallation directory of the app
    """
    for app in apps.get_app_configs():
        yield app


def get_app_label_of_model(model_type: type) -> str:
    """
    get the app owning the given model

    :param model_type: type of the model whose app we need to obtain
    :see: https://stackoverflow.com/a/47436214/1887602
    """
    obj_content_type = ContentType.objects.get_for_model(model_type, for_concrete_model=False)
    return obj_content_type.app_label


def get_name_of_primary_key(model_type: type) -> str:
    """
    Fetch the name of the primary key used in a model

    :param model_type: type of the django_toolbox model (models.Model) which key you want to fetch
    :return: the name of its primary key
    """
    return model_type._meta.pk.name


def get_primary_key_value(model: models.Model) -> any:
    """
    get primary key value of a given model

    :param model: instance of the model whose primary key we need to fetch
    :return: value of the primary key
    """
    name = get_name_of_primary_key(type(model))
    return getattr(model, name)


def are_we_in_migration() -> bool:
    """
    Check if we a re runnign in a migration or not

    :see: https://stackoverflow.com/a/33403873/1887602
    """
    if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
        return True
    else:
        return False


def get_primitive_fields(django_type: type) -> Iterable[models.Field]:
    """
    Fetch an iterable of fields

    :param django_type: model to inspect
    """
    for f in django_type._meta.get_fields():
        if not f.is_relation:
            yield f


def get_unique_field_names(django_type: type) -> Iterable[models.Field]:
    """
    Fetch an iterable of fields which are marked as unique in the associated django_toolbox type

    :param django_type: model to inspect
    """
    for f in django_type._meta.get_fields():
        if f.is_relation:
            continue
        if f.unique:
            yield f


def get_first_unique_field_value(model_instance: models.Model) -> any:
    """
    Get the value of  the first field in the model that is unique

    :param model_instance: instance of a model
    :return: unique field
    """
    for f in model_instance._meta.get_fields():
        if f.is_relation:
            continue
        if f.unique:
           return getattr(model_instance, f.name)


def get_salt_from_password_field(password_field_value: str) -> str:
    """
    fetch the salt from the password field within the database

    :param password_field_value: the string that is stored in the database, as in
    :return: salt used to hash the password
    :see: https://docs.djangoproject.com/en/3.2/topics/auth/passwords/
    """
    return password_field_value.split("$")[2]


