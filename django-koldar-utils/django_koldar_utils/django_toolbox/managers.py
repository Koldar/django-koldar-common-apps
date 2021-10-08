import abc
import uuid
from typing import TypeVar, Generic, Optional, List

import stringcase
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import UserManager
from django.db import models
from django.db.models import Model
from polymorphic.managers import PolymorphicManager

from django_koldar_utils.django_toolbox import django_helpers

TMODEL = TypeVar("TMODEL")


class AbstractManagerMeta(abc.ABCMeta, type(models.Manager)):
    pass

class IManager(models.Manager, metaclass=AbstractManagerMeta):

    @property
    def model_class(self) -> type:
        """
        class of the model the class is currently managing
        """
        return self.model

    @property
    def MultipleObjectsReturned(self):
        return getattr(self.model_class, "MultipleObjectsReturned")

    @property
    def DoesNotExist(self):
        return getattr(self.model_class, "DoesNotExist")

    @abc.abstractmethod
    def _get(self, *args, **kwargs):
        pass

    def has_at_least_one(self, **kwargs) -> bool:
        """
        Check if there is at least one model associated with the specified entry.

        :param kwargs: the same as Manager.get
        """
        try:
            self._get(**kwargs)
            return True
        except self.DoesNotExist:
            return False
        except self.MultipleObjectsReturned:
            return True

    def has_at_most_one(self, **kwargs) -> bool:
        """
        Check if there is at least one model associated with the specified entry.

        :param kwargs: the same as Manager.get
        """
        try:
            self._get(**kwargs)
            return True
        except self.DoesNotExist:
            return True
        except self.MultipleObjectsReturned:
            return False

    def has_exactly_one(self, **kwargs) -> bool:
        """
        Check if there is exactly one model associated with the specified entry.

        :param kwargs: the same as Manager.get
        """
        try:
            self._get(**kwargs)
            return True
        except self.DoesNotExist:
            return False
        except self.MultipleObjectsReturned:
            return False

    def find_only_or_fail(self, **kwargs) -> TMODEL:
        """
        Find the only one element in the model. Raises exception if either zero or more items are fetched isntead


        """
        try:
            return self._get(**kwargs)
        except self.DoesNotExist:
            raise self.DoesNotExist(f"{self.model_class.__name__} with values {kwargs} does not exist")
        except self.MultipleObjectsReturned:
            raise self.MultipleObjectsReturned(f"there are multiple {self.model_class.__name__} with values {kwargs}!")

    def find_only_or_none(self, **kwargs) -> Optional[TMODEL]:
        """
        Alias of :find_only_or_None:
        :param kwargs: kwargs that will be injected into filter or get.
        :return: the only row satisfying the filter or None if there are multiple rows or none of them.
        """
        return self.find_only_or_None(**kwargs)

    def find_only_or_None(self, **kwargs) -> Optional[TMODEL]:
        """
        Find the only entry in the model. If there is not or there are multiple, return None
        """
        try:
            return self._get(**kwargs)
        except self.DoesNotExist:
            return None
        except self.MultipleObjectsReturned:
            return None


class OnlyActiveManagerMixIn(models.Manager):
    """
    A mixin that should be attach only to a django_toolbox manager.
    With this, the manager is now capable to consider only rows whose active field (assumed to be boolean) is True.
    The name of the active field to consider is specified by active_field_name.

    If the model does not contains an "active" flag, we will do nothing. If you know that active flag is
    present, consider setting ASSUME_ACTIVE_IS_PRESENT to improve performances

    You can further customize the mixin by manually setting ACTIVE_FLAG_NAME flag (in combo with
    create_manager_instance_with_class_attribute)
    """

    ACTIVE_FLAG_NAME = "active"
    ASSUME_ACTIVE_IS_PRESENT = False

    def active_field_name(self) -> str:
        return OnlyActiveManagerMixIn.ACTIVE_FLAG_NAME

    def assume_active_is_present(self) -> bool:
        return OnlyActiveManagerMixIn.ASSUME_ACTIVE_IS_PRESENT

    def get_queryset(self):
        if self.assume_active_is_present() or hasattr(self.model, self.active_field_name()):
            return super(models.Manager, self).get_queryset().filter(**{self.active_field_name(): True})
        else:
            return super(models.Manager, self).get_queryset()

    def _get(self, *args, **kwargs):
        if self.assume_active_is_present() or hasattr(self.model, self.active_field_name()):
            kwargs = dict(kwargs)
            kwargs[self.active_field_name()] = True
        return super().get_queryset().get(*args, **kwargs)

    def set_active_flag_to(self, instance: models.Model, enable: bool) -> bool:
        """
        Set the active flag of this instance to a specified value.

        We will not persist the changes we have made. You have to manually set them

        :param instance: instance to chec
        :param enable: true if we want to active the modeol, false otherwis
        :return: true if the model had an active field, false otherwise
        """
        return django_helpers.set_active_flag_to(instance, enable)

    def is_active_flag_active(self, instance: models.Model) -> bool:
        """
        Check if the active flag value of this instance

        :param instance: instance to check
        :return: true if the model is active, false otherwise
        """
        return django_helpers.is_active_flag(instance, True)


#todo readd Generic[TMODEL],
class ExtendedPolymorphicManager(IManager, PolymorphicManager):

    def _get(self, *args, **kwargs):
        return self.model_class._default_manager.get(*args, **kwargs)


#todo readd Generic[TMODEL],
class ExtendedManager(IManager, OnlyActiveManagerMixIn):
    """
    A manager which provides common utilities.
    If you use this manager, we automatically filter out inactive entries.
    Inactive entries are detected via the field name "active_field_name"
    """

    def _get(self, *args, **kwargs):
        return OnlyActiveManagerMixIn._get(self, *args, **kwargs)


#todo readd Generic[TMODEL],
class ExtendedUserManager(UserManager, IManager, OnlyActiveManagerMixIn):
    """
    Extension of the UserManager implementation.
    If you use this manager, we automatically filter out inactive entries.
    Inactive entries are detected via the field name "active_field_name"
    """

    def _get(self, *args, **kwargs):
        return OnlyActiveManagerMixIn._get(self, *args, **kwargs)


def create_manager_instance_with_class_attribute(base_classes: List[type], **kwargs) -> models.Manager:
    """
    Create a new class representing a manager where you can specify some class attributes.
    This is useful because in this way you can pass arguments to a manager.

    A downside is that we create an "anonymous" manager (its name is gibberish

    :see: https://stackoverflow.com/a/39147144
    """
    new_uuid = uuid.uuid4()

    result = type(
        f"CustomManager{stringcase.snakecase(new_uuid)}",
        (models.Manager, *base_classes),
        {
            **kwargs
        }
    )
    return result()


def create_extended_manager(**kwargs):
    """
    Create an extended manager that you can customize. The kwargs are the same the ones in OnlyActiveManagerMixIn
    """
    return create_manager_instance_with_class_attribute(
        base_classes=[IManager, OnlyActiveManagerMixIn],
        **kwargs
    )


class StandardOnlyActiveManager(OnlyActiveManagerMixIn):
    """
    A manager that consider only rows whose actve field is True.
    The name of the field is hardcoded to be "active"
    """

    ACTIVE_FLAG_NAME = "active"


class StandardOnlyIsActiveManager(OnlyActiveManagerMixIn):
    """
    A manager that consider only rows whose actve field is True.
    The name of the field is hardcoded to be "is_active"
    """
    ACTIVE_FLAG_NAME = "is_active"




