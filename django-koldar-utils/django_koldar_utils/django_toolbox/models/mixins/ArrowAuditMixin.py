from django.db import models
from django_currentuser.db.models import CurrentUserField

from django_koldar_utils.django_toolbox.Orm import Orm
from django_koldar_utils.django_toolbox.fields.ArrowField import ArrowField
from django_koldar_utils.django_toolbox.models.mixins.ActiveMixIn import ActiveMixIn


class ArrowAuditMixIn(models.Model):
    """
    A mixin that allows you to automatically add the user that has created, delete or updated a particular model.
    We use "arrow" to convert models
    """
    class Meta:
        abstract = True

    created_at = ArrowField(auto_now_add=True, help_text="Time when the row has been created")
    updated_at = ArrowField(auto_now=True, help_text="Latest time when the row has been updated")
    created_by = CurrentUserField(related_name=Orm.DO_NOT_CREATE_INVERSE_RELATION, help_text="User that has created this row")
    updated_by = CurrentUserField(related_name=Orm.DO_NOT_CREATE_INVERSE_RELATION, on_update=True, help_text="User that has performed the last operation on this row")