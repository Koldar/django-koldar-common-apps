from typing import Optional

from arrow import Arrow
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import models

from django_koldar_utils.django_toolbox.Orm import Orm
from koldar_utils.functions import secrets_helper


class ForgetTokenMixin(models.Model):
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
        description="The time when the forget_password_token was created. Used to detect if the token is expired")
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

    def try_reset_password(self, new_password: str, actual_forget_token: str):
        """
        Reset the password by using a forget token sent via mail
        """
        # check if the there is a forget password token valid
        if self.forget_password_token != actual_forget_token:
            self._on_forget_token_invalid()
        if not self.has_valid_forget_token:
            self._on_forget_token_invalid()

        # update password and clear the reset toke

        salt = secrets_helper.get_random_alphanum_str(16)
        self.password = make_password(new_password, salt=salt)
        self.forget_password_token = None
        self.forget_password_token_creation_date = None
        self.save()

    def _on_forget_token_invalid(self):
        """
        Method invoked if we detected an invalid forget token
        """
        raise ValueError(f"An invalid forget token has been detected! Token will expire at {self.forget_token_expiration_time}")

    def _on_forget_token_already_present(self):
        """
        Method invoked if we have detected that a forget token is still valid
        """
        raise ValueError(f"A forget token has already been send. Token will expire at {self.forget_token_expiration_time}!")

    @classmethod
    def try_sending_forget_token_mail(cls, email: str):
        """
        Send to the email of this user a forget token mail.
        If we cannot send a forget token, we will raise an exception

        :param email: mail to send the forget token to. Might not be present in the system
        """

        UserModel = get_user_model()
        user = UserModel.objects.find_only_or_fail(email=email)

        # check if the there is a forget password token valid
        if user.has_valid_forget_token:
            user._on_forget_token_already_present()

        # we need to refresh the forget token
        user.forget_password_token = secrets_helper.get_random_alphanum_str(300)
        user.forget_password_token_creation_date = Arrow.utcnow()
        user.save()

        # send email
        user.email_user(
            subject="Reset your email",
            message=f"link is {user.forget_password_token}. The token will expire {user.forget_password_token_creation_date.isoformat()}. Thanks"
        )