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

    :param model_type: type of the django model (models.Model) which key you want to fetch
    :return: the name of its primary key
    """
    return model_type._meta.pk.name


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


