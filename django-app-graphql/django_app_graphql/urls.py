from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django_app_graphql.conf import DjangoAppGraphQLAppConf
from django.contrib import admin
import logging

urlpatterns = []
LOG = logging.getLogger(__name__)
settings = DjangoAppGraphQLAppConf()

enable_graphiql = settings.EXPOSE_GRAPHIQL
backend = settings.BACKEND_TYPE

if backend == "ariadne":
    # ###################################################################
    # ###################### ARIADNE ####################################
    # ###################################################################
    from ariadne import ObjectType


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


    view = get_endpoint_from_ariadne(enable_graphiql)

elif backend == "graphene":
    # ###################################################################
    # ######################### GRAPHENE ################################
    # ###################################################################

    def get_endpoint_from_graphene(enable_graphiql: bool):

        if settings.INCLUDE_UPLOAD_MUTATION:
            LOG.info(f"Including FileUploadGraphQLView, since we want to upload mutations...")
            from graphene_file_upload.django import FileUploadGraphQLView
            return FileUploadGraphQLView.as_view(graphiql=enable_graphiql)
        else:
            from graphene_django.views import GraphQLView
            return GraphQLView.as_view(graphiql=enable_graphiql)


    view = get_endpoint_from_graphene(enable_graphiql)
else:
    raise ValueError(f"backend must be ariadne or graphene, intead it was {backend}!")


urlpatterns.append(path(
    settings.GRAPHQL_SERVER_URL,
    csrf_exempt(view)
))

