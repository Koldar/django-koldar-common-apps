import abc
from typing import TypeVar, Optional, Set, Generic

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import Permission

TUSER = TypeVar("TUSER")
TPERMISSION = TypeVar("TPERMISSION")
TUSER_ID = TypeVar("TUSER_ID")


class AbstractDjangoBackend(Generic[TUSER, TUSER_ID, TPERMISSION], BaseBackend, abc.ABC):
    """
    An abstract class that allows you to implement a django_toolbox backend using the content assist. Does not
    provide additional capabilities

    .. ::code-block:: python

        class MyBackend(AbstractBackend):

            def authenticate(self, request, **kwargs):
                if "username" not in kwargs:
                    return None
                if "password" not in kwargs:
                    return None
                username = kwargs["username"]
                password = kwargs["password"]
                # do authentication
                return user
    """

    @abc.abstractmethod
    def authenticate(self, request, **kwargs) -> Optional[TUSER]:
        """
        Tries to authenticate the request.

        :param request: the request to authenticate
        :param kwargs: additional arguments. Inside them are specified the authentication parameters used by this backend
        :return: None if the authentication is not possible, the user is the authentication succeeded
        :raises PermissionDenied: if the authentication failed
        """
        pass

    @abc.abstractmethod
    def get_user(self, user_id: TUSER_ID) -> Optional[TUSER]:
        """
        The get_user method takes a user_id – which could be a username, database ID or whatever,
        but has to be the primary key of your user object – and returns a user object or None.
        """
        pass

    @abc.abstractmethod
    def get_user_permissions(self, user_obj: TUSER, obj=None) -> Set[TPERMISSION]:
        """
        Fetch all the permission explicitly added to this specific user. In a user-group-permissions
        database model, it is associated with the user-permission relationship

        :param user_obj: user whose permissions we need to fetch
        :return: set of permissions explicitly added to the user, or empty set if the user has
            explicitly attached no permissions
        """
        pass

    @abc.abstractmethod
    def get_group_permissions(self, user_obj: TUSER, obj=None) -> Set[TPERMISSION]:
        """
        Fetch all the permission explicitly added to every group of this specific user. In a user-group-permissions
        database model, it is associated with the group-permission relationship

        :param user_obj: user whose permissions we need to fetch
        :return: set of permissions explicitly added to the user via the groups, or empty set if the user
            has explicitly attached no permissions via groups
        """
        pass

    def get_all_permissions(self, user_obj: TUSER, obj=None) -> Set[TPERMISSION]:
        """
        Get all the permissions available to the user. Convenience method

        :param user_obj: user to consider
        :return: set of all the permissions available to the user
        """
        return super().get_all_permissions(user_obj, obj)

    def has_perm(self, user_obj: TUSER, perm: TPERMISSION, obj=None) -> bool:
        """
        Check if a user has a partiular permission

        :param perm: permission to check. It may be possible that the object is not an instance of TPERMISSION.
            It may as well be a string representation of it
        :return: true if the user has the specified permission, false otherwise
        """
        assert isinstance(perm, Permission), f"permission {perm} is not of type TPERMISSION"
        return super().has_perm(user_obj, perm, obj)

