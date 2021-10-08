from django.db import models
from django.db.models import Case
from django.db.models import Value as V
from django.db.models import When
from django.utils import timezone

from django_graphene_authentication.conf import settings


class RefreshTokenQuerySet(models.QuerySet):

    def expired(self):
        expires = timezone.now() - settings.JWT_REFRESH_EXPIRATION_DELTA
        return self.annotate(
            expired=Case(
                When(created__lt=expires, then=V(True)),
                output_field=models.BooleanField(),
                default=V(False),
            ),
        )
