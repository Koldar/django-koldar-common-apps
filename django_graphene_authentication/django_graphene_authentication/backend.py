import abc
from typing import Set, Optional, Dict

import jwt
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from jwt import exceptions as jwt_exceptions, DecodeError
from django.apps import apps
from django.conf import settings
from django.http import HttpRequest
from django_koldar_utils.django_toolbox.AbstractDjangoBackend import AbstractDjangoBackend, TUSER, TPERMISSION, TUSER_ID

from django_graphene_authentication.utils import get_authenticating_token


class AbstractAuthenticateViaToken(AbstractDjangoBackend[any, any, Permission]):
    """
    A backend that uses a token to authenticate the user.

    This backend enters in action when the Json
    If the user inject an token, what we need to do is to authenticate the user. Ho we have retireved such a token
    is not a concern of the authentication backend.

    Since when authenticating we loop ove backend, this backend can be temporary disabled by overwriting
    the function enable_backend
    """

    def authenticate(self, request, **kwargs) -> Optional[TUSER]:
        token = kwargs["token"]
        if token is None:
            # backend not applicable
            return None
        del kwargs["token"]
        if not self.enable_backend(request, token, **kwargs):
            return None

        payload = self._get_payload(token, request, **kwargs)
        user = self._get_user_by_payload(payload, request, **kwargs)
        self.do_after_user_authenticated(request, token, user, payload, **kwargs)

        return user

    def get_user(self, user_id: TUSER_ID) -> Optional[TUSER]:
        User: type = get_user_model()
        return User.objects.get(pk=user_id)

    def enable_backend(self, request, token, **kwargs) -> bool:
        if request is None:
            return False
        return True

    @abc.abstractmethod
    def do_after_user_authenticated(self, request: HttpRequest, authenticating_token: str, user: any, payload: any, **kwargs):
        """
        Code called each time an authenticatng token is used to authenticate a new user

        :param request: http request
        :param authenticating_token: token used to autrhentication
        :param user: authenticated user
        :param payload: decoded token
        :param kwargs: graphql args
        :return:
        """

        pass

    def jwt_token_public_key(self) -> Optional[str]:
        """
        publi key that has generated the token used to authenticate the user

        :return: publick key of the token that we need to decode in order to authenticate the user
        """
        pass

    def jwt_token_secret_key(self) -> Optional[str]:
        """
        Symmetric key that we are going to use to validate the token.
        Used only if the public key is left None
        :return:
        """
        return None

    def jwt_token_verify_expiration(self) -> bool:
        """
        If true, we will verify if the token used to authenticate has been expired or not
        :return:
        """
        return True

    def jwt_token_verify(self) -> bool:
        """
        if true, we will verify if the token signature correctly match
        :return:
        """
        return True

    def jwt_token_leeway(self) -> int:
        return 0

    def jwt_token_audience(self) -> Optional[str]:
        return None

    def jwt_token_issuer(self) -> Optional[str]:
        return None

    def jwt_token_algorithm(self) -> Optional[str]:
        return "HS256"

    def jwt_decode_handle(self, token, request: HttpRequest, **kwargs):
        if self.jwt_token_public_key() is None and self.jwt_token_secret_key() is None:
            raise jwt.DecodeError(f"Cannot decode token. You need to configure either jwt_access_token_public_key or jwt_access_token_secret_key to be non None!")
        return jwt.decode(
            token,
            self.jwt_token_public_key() or self.jwt_token_secret_key(),
            options={
                'verify_exp': self.jwt_token_verify_expiration(),
                'verify_aud': self.jwt_token_audience() is not None,
                'verify_signature': self.jwt_token_verify(),
            },
            leeway=self.jwt_token_leeway(),
            audience=self.jwt_token_audience(),
            issuer=self.jwt_token_issuer(),
            algorithms=[self.jwt_token_algorithm()],
        )

    def jwt_expired_token_detected(self, token, request: HttpRequest, **kwargs):
        raise jwt_exceptions.ExpiredSignatureError(f"token {token} is expired")

    def jwt_decode_error_detected(self, token, request: HttpRequest, **kwargs):
        raise jwt_exceptions.DecodeError(f"token {token} cannot be decoded. Usually this is because you have written the wrong symmetric/asymmetric keys or if the algorithm chosen differs from the source of the token")

    def jwt_invalid_token_detected(self, token, request: HttpRequest, **kwargs):
        raise jwt_exceptions.InvalidTokenError(f"{token} is invalid")

    def _get_payload(self, token: str, request: HttpRequest, **kwargs):
        """
        decode the token and fetch the payload

        :param token: token to decode
        :param request: http request
        :return:
        """
        payload = None
        try:
            payload = self.jwt_decode_handle(token, request, **kwargs)
        except jwt.ExpiredSignatureError:
            self.jwt_expired_token_detected(token, request, **kwargs)
        except jwt.DecodeError:
            self.jwt_decode_error_detected(token, request, **kwargs)
        except jwt.InvalidTokenError:
            self.jwt_invalid_token_detected(token, request, **kwargs)
        return payload

    @abc.abstractmethod
    def _get_user_by_payload(self, payload: any, request: HttpRequest, **kwargs) -> any:
        """
        fetch the user. You can override the method

        :param payload: decoded token
        :param request: http request
        :param kwargs: graphql args
        :return: user
        """
        pass

    def get_user_by_payload(self, payload: any, request: HttpRequest, **kwargs) -> any:
        """
        fetch the user from the payload. Youi should not override this method

        :param payload: decoded token
        :param request: http request
        :param kwargs: graphql params
        :return: user
        """
        try:
            user = self._get_user_by_payload(payload, request, **kwargs)
        except Exception:
            user = None

        if user is not None and not getattr(user, 'is_active', True):
            raise ValueError(f"User {user} is disabled")
        return user


class AbstractAuthenticateViaAccessToken(AbstractAuthenticateViaToken):
    """
    A backend that uses an access_token to authenticate the user.

    This backend enters in action when the Json
    If the user inject an access_token, what we need to do is to authenticate the user.
    """
    pass


class AbstractStandardAuthenticateViaAccessToken(AbstractAuthenticateViaAccessToken, ModelBackend, abc.ABC):
    """
    After authenticating a user via an access token, we will the authorization fields (permissions)
    by polling the database as in django style. You only need to set the authentication token name.

    We assume you can only authenticate ith access_token via a "login mutation". We also assume that such a mutation
    set "are_we_authenticating_from_login_mutation" to True. In this in any other case (e.g., via a graphql middleware)
    autheentication with access_token fails.
    """

    def do_after_user_authenticated(self, request: HttpRequest, authenticating_token: str, user: any, payload: any,
                                    **kwargs):
        pass

    def enable_backend(self, request, token, **kwargs) -> bool:
        if not super().enable_backend(request, token, **kwargs):
            return False
        if not getattr(request, 'are_we_authenticating_from_login_mutation', False):
            # we want to authenticate ONLY if we are inside the authentication mutation.
            return False
        return True

    def __init__(self):
        super(AbstractAuthenticateViaAccessToken, self).__init__()
        super(ModelBackend, self).__init__()

    def get_user_permissions(self, user_obj: TUSER, obj=None) -> Set[Permission]:
        return super(ModelBackend, self)._get_permissions(user_obj, obj, 'user')

    def get_group_permissions(self, user_obj: TUSER, obj=None) -> Set[Permission]:
        return super(ModelBackend, self)._get_permissions(user_obj, obj, 'group')

    def _get_user_by_payload(self, payload: any, request: HttpRequest, **kwargs) -> any:
        UserModel = get_user_model()
        user_id = payload["sub"]
        return UserModel._default_manager.get_by_natural_key(user_id)


class AbstractStandardAuthenticateViaApiTokenAuthenticationBackend(AbstractAuthenticateViaAccessToken):
    """
    This authentication backend allows you to authenticate if you have a api_token. If you have it (either
    from a graphql argument or inside a HTTP authorization field) you can use this authentication method.

    Since api_token is used to authenticate the user, but not to fetch authorizations (i.e., permissions),
    this backend set the permission to empty
    """

    def do_after_user_authenticated(self, request: HttpRequest, authenticating_token: str, user: any, payload: any,
                                    **kwargs):
        pass

    def enable_backend(self, request, token, **kwargs) -> bool:
        """
        We need at elast a token and a request to authenticatethe user
        """
        return super(AbstractAuthenticateViaAccessToken, self).enable_backend(request, token, **kwargs)

    def get_user_permissions(self, user_obj: any, obj=None) -> Set[Permission]:
        # permissions are not set with this backend, since this backend is run after the access_token one
        return set()

    def get_group_permissions(self, user_obj: any, obj=None) -> Set[Permission]:
        # permissions are not set with this backend, since this backend is run after the access_token one
        return set()
