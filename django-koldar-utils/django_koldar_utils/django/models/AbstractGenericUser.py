from typing import Optional, Iterable

from arrow import Arrow
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Permission, Group
from django.core.mail import send_mail

from django.db import models
from django_koldar_utils.django.Orm import Orm
from django_koldar_utils.django.managers import ExtendedUserManager
from django_koldar_utils.django.models.ArrowAuditMixin import ArrowAuditMixIn


class AbstractGenericUser(AbstractBaseUser, ArrowAuditMixIn, PermissionsMixin):
    """
    A class that substitute the standard User in django framework. Used to explicitly differentiate with the base user
    class that we are going to use in this django project to store each user additional properties
    """
    class Meta:
        db_table = Orm.create_table_name("User")
        default_permissions = ()
        abstract = True
    objects = ExtendedUserManager()

    username = Orm.required_unique_string(
        description="Username of the user. Used in the authentication method. Must be unique,")
    email = Orm.required_email(description="email address used for resetting the password")
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
    active = Orm.required_boolean(description="If true, the user can log and work withint the system. False otherwise.",
                                  default_value=True)
    is_superuser = Orm.required_boolean(description="True if this user is an admin, False otherwise",
                                        default_value=False)
    is_staff = models.BooleanField(help_text="Designates whether the user can log into this admin site.", default=False)

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

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

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Send an email to this user.

        :param subject: suvject of the email
        :param message. body of the message to send
        :param from_email: the entity that sends this email
        :param kwargs: arguments to pass to the mail server
        """
        send_mail(subject, message, from_email, [getattr(self, self.EMAIL_FIELD)], **kwargs)

    def get_all_permissions_objects(self) -> Iterable[Permission]:
        """
        Fetches all the permissions the user currently has

        :return: iterable of all the permissions the user currently has
        """
        result = set()
        for x in self.user_permissions.all():
            result.add(x)
        g: Group
        for g in self.groups.all():
            for p in g.permissions.all():
                result.add(p)
        return list(result)