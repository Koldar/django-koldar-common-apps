import abc
from typing import TypeVar, Generic, Optional

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import UserManager
from django.db import models
from django.db.models import Model
from polymorphic.managers import PolymorphicManager

TMODEL = TypeVar("TMODEL")


class IManager(abc.ABC):

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


#todo readd Generic[TMODEL],
class ExtendedPolymorphicManager(IManager, PolymorphicManager):

    def _get(self, *args, **kwargs):
        return self.model_class._default_manager.get(*args, **kwargs)


#todo readd Generic[TMODEL],
class ExtendedManager(IManager, models.Manager):
    """
    A manager which provides common utilities
    """

    def _get(self, *args, **kwargs):
        return self.model_class._default_manager.get(*args, **kwargs)


#todo readd Generic[TMODEL],
class ExtendedUserManager(IManager, UserManager):
    """
    Extension of the UserManager implementation
    """

    def _get(self, *args, **kwargs):
        return self.model_class._default_manager.get(*args, **kwargs)
