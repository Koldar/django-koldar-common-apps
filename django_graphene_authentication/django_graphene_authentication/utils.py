from calendar import timegm
from datetime import datetime
from typing import Optional
import logging

from django.apps import apps
from django.http import HttpRequest

from django_graphene_authentication.conf import settings


LOG = logging.getLogger(__name__)


def get_refresh_token_model():
    return apps.get_model(settings.JWT_REFRESH_TOKEN_MODEL)


def get_refresh_token_by_model(refresh_token_model, token, context=None):
    return refresh_token_model.objects.get(token=token, revoked__isnull=True)


def get_authenticating_token(request: HttpRequest, jwt_auth_header_prefix: str = None, token_authentication_header_name: str = None, jwt_graphql_token_argument_name: str = None, allow_argument: bool = True, **kwargs) -> Optional[str]:
    """
    Fetch a token from the graphql request that is used to authenticate the user
    We will first look in the grphql mutation/query arguments (if the configuration allows it).
    If not, look it at the authoprizationc header

    :param request: http request
    :param jwt_auth_header_prefix:
    :param token_authentication_header_name: name of a HTTP header containing the token
    :param jwt_graphql_token_argument_name: name of a grpahql argum,ent representing the token
    :param allow_argument:
    :param kwargs: graphql mutation/query arguments
    :return: token used to authorization
    """
    result = get_authentication_token_in_graphql_argument(
        request=request,
        jwt_graphql_token_argument_name=jwt_graphql_token_argument_name,
        allow_argument=allow_argument,
        **kwargs
    )
    if result is not None:
        return result
    result = get_authentication_token_from_http_authorization(
        request=request,
        token_authentication_header_name=token_authentication_header_name,
        jwt_auth_header_prefix=jwt_auth_header_prefix,
    )
    if result is not None:
        return result
    return None


def get_authentication_token_from_http_authorization(request: HttpRequest, token_authentication_header_name: str, jwt_auth_header_prefix: str) -> str:
    """
    Fetch the token from the http request by looking at the HTTP authorization section.

    :param request: request containing a token.
    :param token_authentication_header_name: name of the HTTP header we need to scout
    :param jwt_auth_header_prefix: domain of the token (e.g., jwt, bearer)
    :return: token that will be use to authenticate the request
    """
    auth = request.META.get(token_authentication_header_name, '').split()
    if len(auth) == 0:
        # header not found
        return None
    if len(auth) == 2:
        # compliant header
        # auth is a string like "jwt askfhdfklghdjhdhdfòlhdo"
        prefix = jwt_auth_header_prefix

        return auth[1]
    else:
        # invalid header
        LOG.warning(f"invalid header {token_authentication_header_name} content! We will act as if were not an authentiction header at all")
        return None


def get_authentication_token_in_graphql_argument(request: HttpRequest, jwt_graphql_token_argument_name: str = None, allow_argument: bool = True, **kwargs) -> Optional[str]:
    """
    Fetch the authentication toklen from the graphql arguments of this resolve mechanism

    :param request: request whose token we need to fetch
    :param jwt_graphql_token_argument_name: name of the token we need to fetch
    :param allow_argument: true if we should scout the token in the arguments as wll
    :param kwargs:
    :return: token hat we need to use to authenticate the request, or None if the token could not be found
    """
    if allow_argument:
        # fetch the arguments of this resolve request
        return dict(kwargs).get(jwt_graphql_token_argument_name)
        # input_fields = kwargs.get('input')
        #
        # if isinstance(input_fields, dict):
        #     kwargs = input_fields
        #
        # # fetch the token
        # return kwargs.get(jwt_api_token_name)
    return None

# # imported from graphql-jwt
#
# from calendar import timegm
# from datetime import datetime
#
# import django
# from django.contrib.auth import get_user_model
# from django.utils.translation import gettext as _
#
# import jwt
#
#

#
#

#
#
# def jwt_decode(token, context=None):
#     return jwt.decode(
#         token,
#         jwt_settings.JWT_PUBLIC_KEY or jwt_settings.JWT_SECRET_KEY,
#         options={
#             'verify_exp': jwt_settings.JWT_VERIFY_EXPIRATION,
#             'verify_aud': jwt_settings.JWT_AUDIENCE is not None,
#             'verify_signature': jwt_settings.JWT_VERIFY,
#         },
#         leeway=jwt_settings.JWT_LEEWAY,
#         audience=jwt_settings.JWT_AUDIENCE,
#         issuer=jwt_settings.JWT_ISSUER,
#         algorithms=[jwt_settings.JWT_ALGORITHM],
#     )
#
#

#
#
# def get_credentials(request, **kwargs):
#     return (get_token_argument(request, **kwargs) or
#             get_http_authorization(request))
#
#
# def get_payload(token, context=None):
#     try:
#         payload = jwt_settings.JWT_DECODE_HANDLER(token, context)
#     except jwt.ExpiredSignatureError:
#         raise exceptions.JSONWebTokenExpired()
#     except jwt.DecodeError:
#         raise exceptions.JSONWebTokenError(_('Error decoding signature'))
#     except jwt.InvalidTokenError:
#         raise exceptions.JSONWebTokenError(_('Invalid token'))
#     return payload
#
#
# def get_user_by_natural_key(username):
#     UserModel = get_user_model()
#     try:
#         return UserModel._default_manager.get_by_natural_key(username)
#     except UserModel.DoesNotExist:
#         return None
#
#
# def get_user_by_payload(payload):
#     username = jwt_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER(payload)
#
#     if not username:
#         raise exceptions.JSONWebTokenError(_('Invalid payload'))
#
#     user = jwt_settings.JWT_GET_USER_BY_NATURAL_KEY_HANDLER(username)
#
#     if user is not None and not getattr(user, 'is_active', True):
#         raise exceptions.JSONWebTokenError(_('User is disabled'))
#     return user
#
#
def refresh_has_expired(orig_iat, context=None):
    """
    Check if the token has expired or not
    :param orig_iat:
    :param context:
    :return:
    """
    exp = orig_iat + settings.JWT_REFRESH_EXPIRATION_DELTA.total_seconds()
    return timegm(datetime.utcnow().utctimetuple()) > exp
#
#
# def set_cookie(response, key, value, expires):
#     kwargs = {
#         'expires': expires,
#         'httponly': True,
#         'secure': jwt_settings.JWT_COOKIE_SECURE,
#         'path': jwt_settings.JWT_COOKIE_PATH,
#         'domain': jwt_settings.JWT_COOKIE_DOMAIN,
#     }
#     if django.VERSION >= (2, 1):
#         kwargs['samesite'] = jwt_settings.JWT_COOKIE_SAMESITE
#
#     response.set_cookie(key, value, **kwargs)
#
#
# def delete_cookie(response, key):
#     response.delete_cookie(
#         key,
#         path=jwt_settings.JWT_COOKIE_PATH,
#         domain=jwt_settings.JWT_COOKIE_DOMAIN,
#     )
