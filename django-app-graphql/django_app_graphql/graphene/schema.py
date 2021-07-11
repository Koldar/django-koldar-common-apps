# This represents all the graphQL queries and mutations
import logging
import os

import graphene
import stringcase
import graphene_federation

from django_koldar_utils.graphql.graphql_decorators import graphql_subquery, graphql_submutation
from django_app_graphql.conf import settings

LOG = logging.getLogger(__name__)

SCHEMA: graphene.Schema = None

# Dummy query mutations
class DummyMutation(object):
    class Arguments:
        name = graphene.String()

    result = graphene.String()

    def mutate(self, name: str):
        return DummyMutation(f"hello {name}!")


class DummyQuery(object):
    yields_true = graphene.Boolean(default_value=True)
    """
    A query that always yields True
    """
    yields_foo = graphene.String()
    """
    A query that always yields Foo, as a lambda
    """
    yields_name = graphene.String(name=graphene.String())
    """
    A query that requires a string as "name" and outputs hello name!
    """

    def resolve_yields_foo(root, info):
        return "Foo"

    def resolve_yields_name(root, info, name: str):
        return f"hello {name}"


def create_schema():
    # Query
    if len(graphql_subquery.query_classes) == 0 and settings.DJANGO_APP_GRAPHQL["ADD_DUMMY_QUERIES_IF_ABSENT"]:
        # add a query. graphene requires at least one
        LOG.warning(f"No queries present. Add some dummy queries")
        graphql_subquery.query_classes.append(DummyQuery)

    LOG.info(f"queries are: {graphql_subquery.query_classes}")
    bases = tuple(graphql_subquery.query_classes + [graphene.ObjectType, object])
    for cls in bases:
        if cls.__name__ in ("object", "ObjectType", "ObjectTypeOptions"):
            continue
        LOG.info("Including '{}' in global GraphQL Query...".format(cls.__name__))
    Query = type('Query', bases, {})

    # Mutation
    if len(graphql_submutation.mutation_classes) == 0 and settings.DJANGO_APP_GRAPHQL["ADD_DUMMY_MUTATIONS_IF_ABSENT"]:
        # add a query. graphene requires at least one
        graphql_submutation.mutation_classes.append(DummyMutation)

    LOG.info(f"mutations are: {graphql_submutation.mutation_classes}")
    bases = tuple(graphql_submutation.mutation_classes + [graphene.Mutation, graphene.ObjectType, object])
    properties = {}
    for cls in bases:
        # some base classes needs to be ignored since they are not queries or mutations
        if cls.__name__ in ("object", "ObjectType", "ObjectTypeOptions", "Mutation"):
            continue
        LOG.info("Including '{}' in global GraphQL Mutation...".format(cls.__name__))
        try:
            name = stringcase.camelcase(cls.__name__)
            if not hasattr(cls, "_meta") and hasattr(cls, "Meta"):
                # Sometimes a class has "Meta" attribute, but django requires a "_meta" attribute. Add it to the class
                setattr(cls, "_meta", getattr(cls, "Meta"))
            properties[name] = cls.Field()
        except Exception as e:
            LOG.warning(f"Ignoring exception {e} while adding {cls} to mutations!")
            LOG.exception(e)

    Mutation = type('Mutation', bases, properties)

    if settings.DJANGO_APP_GRAPHQL["ENABLE_GRAPHQL_FEDERATION"]:
        LOG.info(f"Building graphQL schema with federation support")
        schema = graphene_federation.build_schema(query=Query, mutation=Mutation)
    else:
        LOG.info(f"Building graphQL schema without federatio nsupport")
        schema = graphene.Schema(query=Query, mutation=Mutation)

    if settings.DJANGO_APP_GRAPHQL["SAVE_GRAPHQL_SCHEMA"] is not None:
        p = settings.DJANGO_APP_GRAPHQL["SAVE_GRAPHQL_SCHEMA"]
        LOG.debug(f"Saving the whole generated graphql schema in {os.path.abspath(p)}")
        with open(p, encoding="utf8", mode="w") as f:
            f.write(str(schema))

    return schema


if SCHEMA is None:
    SCHEMA = create_schema()



