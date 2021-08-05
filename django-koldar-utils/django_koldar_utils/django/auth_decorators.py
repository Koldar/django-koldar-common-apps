import functools
from typing import Optional, Callable, List, Union

from django.contrib.auth.models import Permission


def get_graphql_user_standard(cls, info, *args, **kwargs) -> Optional[any]:
    """
    fetch the usser from a graphql query.


    By default we will look at "user" or at "authenticated_user" info.context variable (which is the http request)
    """
    if hasattr(info.context, 'user'):
        return info.context.user
    elif hasattr(info.context, "authenticated_user"):
        return info.context.authenticated_user
    else:
        return None


def exception_callback(request, *args, **kwargs):
    return ValueError(f"Required authenticated user to gain access to this endpoint.")


def permissions_denied_standard(user, request, missing_permissions=None, *args, **kwargs):
    raise ValueError(
        f"The user {user} do not have the required permissions {', '.join(missing_permissions)} for accessing the function.")


def graphql_ensure_login_required(get_user: Callable[[any, any, any, any], any] = None, exc: Callable[[any, any, any], Exception] = None):
    """
    Generates a decorator that checks if a user is authenticated. If it fails, it generates an exception.
    This decorator can be used only in graphql mutation/query body.
    We assume the decorated function has the following prototype

    def body(root, info, *args, **kwargs):
        pass

    :param get_user: function that fetches the user from the request. If none, we will fetch it by using request.user
    :param exc: function that genrates the exception to raise in case of unsuccessful login.
    first parameter is the request, the second the function *arg and the third the function **kwargs
    :return:
    """

    if get_user is None:
        get_user = get_graphql_user_standard
    if exc is None:
        exc = exception_callback

    def decorator(f):
        @functools.wraps(f)
        def wrapper(cls, info, *args, **kwargs):
            user = get_user(cls, info, *args, **kwargs)
            if user is not None:
                return f(cls, info, *args, **kwargs)
            else:
                raise exc(cls, info, *args, **kwargs)

        return wrapper

    return decorator


def graphql_ensure_user_has_permissions(perm: Union[List[str], str], get_user: Callable[[any, any, any], any] = None, exc: Callable[[any, any, any], Exception] = None, permission_denied_exc: Callable = None):
    """
    A copy of permission_required where the error generates the missing permissions.
    We assume that the decorated function s a grpahene query/mutation body, thus it should follow the following prototype:

    def body(root, info, *args, **kwargs):
        pass

    :param perm: the permissions a user needs to have in order to gain access to the function
    :param get_user: function that fetches the user from the request. If none, we will fetch it by using request.user
    :param exc: function that genrates the exception to raise in case of unsuccessful login.
    :param permission_denied_exc: a function that si called whenever the function detects that the user do not have enough permissions to perform the action
    first parameter is the request, the second the function *arg and the third the function **kwargs
    """

    if get_user is None:
        get_user = get_graphql_user_standard
    if exc is None:
        exc = exception_callback
    if permission_denied_exc is None:
        permission_denied_exc = permissions_denied_standard

    def decorator(f):
        @functools.wraps(f)
        def wrapper(cls, info, *args, **kwargs):
            user = get_user(cls, info, *args, **kwargs)
            if user is None:
                exc(info, *args, **kwargs)

            if isinstance(perm, str):
                perms = (perm,)
            else:
                perms = perm
            # convert permissions codename into Permission objects
            perms = (Permission.objects.get(codename=p) for p in perms)
            missing_permissions = list(filter(lambda p: not user.has_perm(p), perms))

            if len(missing_permissions) > 0:
                permission_denied_exc(user, info.context, missing_permissions, *args, **kwargs)
            return f(cls, info, *args, **kwargs)
        return wrapper
    return decorator