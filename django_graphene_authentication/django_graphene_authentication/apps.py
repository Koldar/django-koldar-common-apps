from django.apps import AppConfig


class DjangoGraphqlApiTokenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_graphene_authentication'

    def ready(self):
        pass
