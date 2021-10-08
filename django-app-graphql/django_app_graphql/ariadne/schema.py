import ariadne
from ariadne import gql, QueryType, MutationType
from ariadne.contrib.federation import make_federated_schema
from django.apps import apps
from koldar_utils.functions import file_helpers
from graphql.type.schema import GraphQLSchema

from django_app_graphql.ariadne.decorators import AriadneSchemaEntityYielder
from django_app_graphql.conf import settings

from django_app_graphql.ariadne import decorators

import logging

from django_app_graphql.ariadne.AbstractScalarType import AbstractScalarType

LOG = logging.getLogger(__name__)


def generate_schema_from_apps() -> GraphQLSchema:
    """
    The function scans your project and apps and fetch all the *.graphql files.

    Then, it builds the schema
    :return:
    """

    files = []

    for app in apps.get_app_configs():
        LOG.info(f"Inspecting app {app.verbose_name} at {app.path}")
        for graphql_file in file_helpers.get_all_files_ending_with(app.path, "graphql"):
            LOG.info(f"Including graphql file {graphql_file}")
            # load file content
            with open(graphql_file, mode="r", encoding="utf8") as f:
                content = f.read()
            files.append(content)
        # now we add all the schema

    typedefs = gql('\n'.join(files))

    y = AriadneSchemaEntityYielder()
    LOG.info(f"number of query resolvers detected: {y.get_total_query_resolvers()}")
    LOG.info(f"number of mutation resolvers detected: {y.get_total_mutation_resolvers()}")
    LOG.info(f"Scalars resolvers detected: {list(map(lambda x: x.name, y.get_scalars()))}")

    stuff_to_register = []
    if y.get_total_query_resolvers() > 0:
        stuff_to_register.append(decorators.query)
    if y.get_total_mutation_resolvers() > 0:
        stuff_to_register.append(decorators.mutation)
    stuff_to_register.extend(list(y.get_scalars()))

    if settings.DJANGO_APP_GRAPHQL["ENABLE_GRAPHQL_FEDERATION"]:
        LOG.info(f"Making a federated schema...")
        return make_federated_schema(
            typedefs,
            *stuff_to_register
        )
    else:
        LOG.info(f"Making a standard schema...")
        return ariadne.make_executable_schema(
            typedefs,
            *stuff_to_register
        )


