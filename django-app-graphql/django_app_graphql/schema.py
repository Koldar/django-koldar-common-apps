# This represents all the graphQL queries and mutations
import logging

import graphene
import stringcase

from django_koldar_utils.graphql.graphql_decorators import graphql_subquery, graphql_submutation

LOG = logging.getLogger(__name__)


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


# Query
if len(graphql_subquery.query_classes) == 0:
    # add a query. graphene requires at least one
    graphql_subquery.query_classes.append(DummyQuery)

LOG.info(f"queries are: {graphql_subquery.query_classes}")
bases = tuple(graphql_subquery.query_classes + [graphene.ObjectType, object])
for cls in bases:
    LOG.info("Including '{}' in global GraphQL Query...".format(cls.__name__))
Query = type('Query', bases, {})


# Mutation
if len(graphql_submutation.mutation_classes) == 0:
    # add a query. graphene requires at least one
    graphql_submutation.mutation_classes.append(DummyMutation)

LOG.info(f"mutations are: {graphql_submutation.mutation_classes}")
bases = tuple(graphql_submutation.mutation_classes + [graphene.Mutation, graphene.ObjectType, object])
properties = {}
for cls in bases:
    LOG.info("Including '{}' in global GraphQL Mutation...".format(cls.__name__))
    try:
        name = stringcase.camelcase(cls.__name__)
        properties[name] = cls.Field()
    except Exception as e:
        LOG.warning(f"Ignoring exception {e} while adding {cls} to mutations")

Mutation = type('Mutation', bases, properties)


schema = graphene.Schema(query=Query, mutation=Mutation)

LOG.debug(f"Logging the whole graphql schema:")
LOG.debug(schema)
