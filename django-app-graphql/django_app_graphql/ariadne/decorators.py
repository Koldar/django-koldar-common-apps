from typing import Dict, Set, Iterable

from ariadne import QueryType, MutationType, ObjectType, ScalarType
from koldar_utils.functions import decorators


class AriadneSchemaEntityYielder(object):
    """
    Object containing all the ariadne information. Used to programmatically gain all the registered entities
    """

    _QUERIES: Dict[str, ObjectType]
    _MUTATIONS: Dict[str, MutationType]
    _SCALARS: Set[ScalarType] = set()

    def get_total_query_resolvers(self) -> int:
        sum = 0
        x: ObjectType
        for x in AriadneSchemaEntityYielder._QUERIES.values():
            sum += len(x._resolvers)
        return sum

    def get_total_mutation_resolvers(self) -> int:
        sum = 0
        x: ObjectType
        for x in AriadneSchemaEntityYielder._MUTATIONS.values():
            sum += len(x._resolvers)
        return sum

    def get_query(self, name: str) -> ObjectType:
        """
        Generates a decorator used to decorate resolvers of a single entity
        Decorator used to register query resolvers
        """
        if name not in AriadneSchemaEntityYielder._QUERIES:
            AriadneSchemaEntityYielder._QUERIES[name] = ObjectType(name)
        return AriadneSchemaEntityYielder._QUERIES[name]

    def _get_mutation(self, name: str) -> MutationType:
        if name not in AriadneSchemaEntityYielder._MUTATIONS:
            AriadneSchemaEntityYielder._MUTATIONS[name] = MutationType()
        return AriadneSchemaEntityYielder._MUTATIONS[name]

    def add_scalar(self, scalar: ScalarType):
        AriadneSchemaEntityYielder._SCALARS.add(scalar)

    def get_scalars(self) -> Iterable[ScalarType]:
        yield from AriadneSchemaEntityYielder._SCALARS

    def get_mutation(self) -> MutationType:
        """
        Decorator used to register mutation resolvers
        """
        return self._get_mutation("Mutation")