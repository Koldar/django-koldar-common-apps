from ariadne import ObjectType
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django_app_graphql.conf import settings
import logging

urlpatterns = []

LOG = logging.getLogger(__name__)


def get_default_schema_from_ariadne(e):
    import ariadne
    from ariadne import gql, QueryType

    typedefs = gql("""
        type Query {
            errorWhileImportingSchema: String!
        }
        """)
    query = ObjectType("Query")

    @query.field("errorWhileImportingSchema")
    def resolve_error(*_):
        return f"Exception was: {e}"

    return ariadne.make_executable_schema(typedefs, query)


def get_endpoint_from_ariadne(enable_graphiql: bool):
    from ariadne.contrib.django.views import GraphQLView
    from django_app_graphql.ariadne.schema import generate_schema_from_apps
    import ariadne
    from ariadne import gql, QueryType

    try:
        schema = generate_schema_from_apps()
    except Exception as e:
        LOG.exception(e)
        schema = get_default_schema_from_ariadne(e)

    return GraphQLView.as_view(schema=schema, introspection=enable_graphiql)


def get_endpoint_from_graphene(enable_graphiql: bool):
    from graphene_django.views import GraphQLView
    return GraphQLView.as_view(graphiql=enable_graphiql)


backend = settings.DJANGO_APP_GRAPHQL["BACKEND_TYPE"]
enable_graphiql = settings.DJANGO_APP_GRAPHQL["EXPOSE_GRAPHIQL"]
if backend == "ariadne":
    view = get_endpoint_from_ariadne(enable_graphiql)
elif backend == "graphene":
    view = get_endpoint_from_graphene(enable_graphiql)
else:
    raise ValueError(f"backend must be ariadne or graphene")

urlpatterns.append(path(
    settings.DJANGO_APP_GRAPHQL["GRAPHQL_SERVER_URL"],
    csrf_exempt(view)
))

