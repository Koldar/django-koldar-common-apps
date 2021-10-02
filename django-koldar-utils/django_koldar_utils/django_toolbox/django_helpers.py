import sys
from typing import Iterable

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.apps import apps


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


