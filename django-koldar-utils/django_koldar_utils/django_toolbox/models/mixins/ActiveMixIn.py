from django.db import models

from django_koldar_utils.django_toolbox.Orm import Orm


class ActiveMixIn(models.Model):
    """
    A mixin that allows you to automatically add the user that has created, delete or updated a particular model.
    We use "arrow" to convert models
    """
    class Meta:
        abstract = True

    active = Orm.required_boolean(
        default_value=True,
        description="""If set, the row should be included in whatever queryset generated"""
    )

