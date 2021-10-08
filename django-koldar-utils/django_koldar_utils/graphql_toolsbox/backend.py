from typing import Set, Optional

from django_koldar_utils.django_toolbox.AbstractDjangoBackend import AbstractDjangoBackend, TUSER, TPERMISSION, TUSER_ID


class GeneralServiceBackend(AbstractDjangoBackend):
    """
    Service tht pass the access token and retrieve the api_token
    """

    def authenticate(self, request, access_token: str, **kwargs) -> Optional[TUSER]:
        pass

    def get_user(self, user_id: TUSER_ID) -> Optional[TUSER]:
        pass

    def get_user_permissions(self, user_obj: TUSER, obj=None) -> Set[TPERMISSION]:
        pass

    def get_group_permissions(self, user_obj: TUSER, obj=None) -> Set[TPERMISSION]:
        pass