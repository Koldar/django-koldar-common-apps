from django.db import models
from django_currentuser.db.models import CurrentUserField

from django_koldar_utils.django.Orm import Orm
from django_koldar_utils.django.fields.ArrowField import ArrowField


class ArrowAuditMixIn(models.Model):
    """
    A mixin that allows you to automatically add the user that has created or updated a particular model
    """
    class Meta:
        abstract = True

    created_at = ArrowField(auto_now_add=True)
    updated_at = ArrowField(auto_now=True)
    active = models.BooleanField()
    created_by = CurrentUserField(related_name=Orm.DO_NOT_CREATE_INVERSE_RELATION)
    updated_by = CurrentUserField(related_name=Orm.DO_NOT_CREATE_INVERSE_RELATION, on_update=True)