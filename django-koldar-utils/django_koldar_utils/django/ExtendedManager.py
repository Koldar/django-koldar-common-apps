from typing import TypeVar, Generic

from django.db import models

TMODEL = TypeVar("TMODEL")


class ExtendedManager(Generic[TMODEL], models.Manager):
    """
    A manager which provides common utilities
    """

    @property
    def model_class(self) -> type:
        """
        class of the model the class is currently managing
        """
        return self.model.__class__

    @property
    def MultipleObjectsReturned(self):
        return getattr(self.model_class, "MultipleObjectsReturned")

    @property
    def DoesNotExist(self):
        return getattr(self.model_class, "DoesNotExist")

    def has_entry(self, **kwargs) -> bool:
        try:
            self.model_class._meta._default_manager.get(**kwargs)
            return True
        except self.DoesNotExist:
            return False

    def find_only_or_fail(self, **kwargs) -> TMODEL:
        return self.model_class._meta._default_manager.get(**kwargs)


