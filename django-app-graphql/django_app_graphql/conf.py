from django.conf import settings
from appconf import AppConf


class DjangoAppGraphQLAppConf(AppConf):
    EXPOSE_GRAPHIQL = True
    """
    If set, we will expose the graphiql UI
    """
    GRAPHQL_SERVER_URL = "/graphql"
    """
    the endpoint where the graphql server is located
    """

