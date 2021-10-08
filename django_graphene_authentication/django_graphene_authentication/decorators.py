import functools
from calendar import timegm
from datetime import timedelta, datetime
from typing import Callable, List, Union, Optional
from django.utils.translation import gettext as _

from django.middleware import csrf
from graphene.utils.thenables import maybe_thenable

from django_graphene_authentication.conf import settings


def get_ensure_refresh_token_decorator(cookie_name: str):
    """
    The generated decorator should be applied to a mutation body function

    :param cookie_name: name of the cookie containing the refresh token
    :return:
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(mutation_instance, info, *args, refresh_token=None, **kwargs):
            if refresh_token is None:
                refresh_token = info.context.COOKIES.get(cookie_name)
                if refresh_token is None:
                    raise ValueError(_('Refresh token is required'))
            result = f(mutation_instance, info, *args, **{"refresh_token": refresh_token, **kwargs})
            return result
        return wrapper
    return decorator


def get_refresh_expiration_decorator(delta: timedelta, refresh_expires_in_name: str):
    """

    :param delta: time after which the token expires.
    :param refresh_expires_in_name: name of the field to add to the payload rpresenting the expiration time
    :return:
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            def on_resolve(payload):
                setattr(payload, refresh_expires_in_name, timegm(datetime.utcnow().utctimetuple()) + delta.total_seconds())
                return payload

            result = f(*args, **kwargs)
            return maybe_thenable(result, on_resolve)
        return wrapper
    return decorator


def get_csrf_rotation_decorator(enable: bool = True):
    """
    Rotate CSRF. Used for security reasons

    Copied from graphql-jwt.
    The generated decorator should be applied to a mutation body function

    :param enable: If true, we will enable the CSRF. Otherwise, the generated decorator does nothing
    :return:
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(mutation_instance, info, *args, **kwargs):
            result = f(mutation_instance, info, *args, **kwargs)
            if enable:
                csrf.rotate_token(info.context)
            return result
        return wrapper
    return decorator


refresh_expiration = get_refresh_expiration_decorator(
    settings.GRAPHENE_AUTHENTICATION_JWT_REFRESH_EXPIRATION_DELTA,
    settings.GRAPHENE_AUTHENTICATION_JWT_REFRESH_EXPIRES_IN_NAME
)
ensure_refresh_token = get_ensure_refresh_token_decorator(settings.GRAPHENE_AUTHENTICATION_JWT_REFRESH_TOKEN_COOKIE_NAME)
csrf_rotation = get_csrf_rotation_decorator(True)