from typing import Optional

from arrow import Arrow
from django.db import models

from django_koldar_utils.django.Orm import Orm


class ForgeTokenMixin(models.Model):
    """
    A mixin you should attach to the user object. This mixin add to the user the capability of a "forget password?".
    At database level, it adds 2 new columns: the forget token and the forget token creation time (used to check if
    the token is still valid).
    """

    class Meta:
        abstract = True

    forget_password_token = Orm.nullable_string(
        description="Token used to verify the reset password string. Present only if the user has initiated the reset password procedure")
    """
    Token used to verify the reset password string. Present only if the user has initiated the reset password procedure
    """
    forget_password_token_creation_date = Orm.nullable_datetime(
        help_text="The time when the forget_password_token was created. Used to detect if the token is expired")
    """
    The time when the forget_password_token was created. Used to detect if the token is expired
    """

    @property
    def has_valid_forget_token(self) -> bool:
        if self.forget_password_token is None:
            return False
        return not self.is_forget_token_expired

    @property
    def forget_token_expiration_time(self) -> Optional[Arrow]:
        """
        Retrieve the UTC time when the forget token (if exists) expires. None if there is no forget token
        """
        if self.forget_password_token_creation_date is None:
            return None
        else:
            c: Arrow = self.forget_password_token_creation_date
            return c.shift(days=+1)

    @property
    def is_forget_token_expired(self) -> bool:
        """
        True if the forget token has been expired. False if not or if the forget token was not present altogether
        """
        if self.forget_password_token_creation_date is None:
            return False
        if Arrow.utcnow() > self.forget_token_expiration_time:
            return True
        return False

    def send_forget_token_mail(self):
        """
        Send a mail to the email address provided during username registration with the expected token.
        """
        raise NotImplementedError()