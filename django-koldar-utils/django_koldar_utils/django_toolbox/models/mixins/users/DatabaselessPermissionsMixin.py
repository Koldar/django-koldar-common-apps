import abc
from typing import TypeVar, List, Set, Generic

from django.contrib.auth.models import _user_get_permissions, _user_has_perm, _user_has_module_perms
from django.db import models

from django_koldar_utils.django_toolbox.models.AbstractModelMetaclass import AbstractModelMetaclass

TPERMISSION = TypeVar("TPERMISSION")


class DatabaselessPermissionsMixin(models.Model):
    """
    Add only the methods necessary to support the Group and Permission of a django_toolbox user implementation.
    It is different from normal PermissionsMixin provided by django_toolbox because that mixin assume 2 relationships:
    groups and permissions. This mixin does not assume them. This structure also does not assume permission type.

    You mau not that this mixin does not actually store the permissions. This is because this mixin
    (that should be attached to the user) calls all the authentication backend and, for each of them,
    call "get_xxx_permissions" methods (if defined)
    to fetch the concrete permissions. In other words, it is the authentication backend that actually
    specifies the permissions, not this mixin
    """

    class Meta:
        abstract = True

    def is_user_superuser(self) -> bool:
        """
        True if the user this class is attached to is a superuser, false otherwise
        """
        return self.is_superuser

    def is_user_active(self) -> bool:
        """
        True if the user is active, false otherwise
        """
        return self.active

    def get_user_permissions(self, obj=None) -> List[TPERMISSION]:
        """
        Return a list of permission strings that this user has directly.
        Query all available auth backends. If an object is passed in,
        return only permissions matching this object.

        We will iteratively checking all the authentication backend registered for this project.
        For that, we will call the function "get_user_permissions". All the permissions will be merge together.

        Note that, this mixin does not dd "groups" and "permissions" model relationship, hence backends using them
        cannot be used!
        """
        return _user_get_permissions(self, obj, 'user')

    def get_group_permissions(self, obj=None) -> Set[TPERMISSION]:
        """
        Return a list of permission strings that this user has through their
        groups. Query all available auth backends. If an object is passed in,
        return only permissions matching this object.

        We will iteratively checking all the authentication backend registered for this project.
        For that, we will call the function "get_user_permissions". All the permissions will be merge together.

        Note that, this mixin does not dd "groups" and "permissions" model relationship, hence backends using them
        cannot be used!
        """
        return _user_get_permissions(self, obj, 'group')

    def get_all_permissions(self, obj=None) -> Set[TPERMISSION]:
        return _user_get_permissions(self, obj, 'all')

    def has_perm(self, perm, obj=None):
        """
        Return True if the user has the specified permission. Query all
        available auth backends, but return immediately if any backend returns
        True. Thus, a user who has permission from a single auth backend is
        assumed to have permission in general. If an object is provided, check
        permissions for that object.
        """
        # Active superusers have all permissions.
        if self.is_user_active() and self.is_user_superuser():
            return True

        # Otherwise we need to check the backends.
        return _user_has_perm(self, perm, obj)

    def has_perms(self, perm_list, obj=None):
        """
        Return True if the user has each of the specified permissions. If
        object is passed, check if the user has all required perms for it.
        """
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        """
        Return True if the user has any permissions in the given app label.
        Use similar logic as has_perm(), above.
        """
        # Active superusers have all permissions.
        if self.is_user_active() and self.is_user_superuser():
            return True

        return _user_has_module_perms(self, app_label)
