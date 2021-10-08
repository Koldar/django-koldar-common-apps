from typing import Dict, Callable, List, Union

from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneArgument, TGrapheneWholeQueryReturnType, \
    TDjangoModelType, TGrapheneType, TGrapheneInputType, TGrapheneQuery, TGrapheneMutation

from django_graphene_crud_generator.generator.AbstractGraphQLMutationGenerator import AbstractGraphQLMutationGenerator
from django_graphene_crud_generator.generator.AbstractGraphQLQueryGenerator import AbstractGraphQLQueryGenerator
from django_graphene_crud_generator.generator.LambdaGraphQLMutationGenerator import LambdaGraphQLMutationGenerator
from django_graphene_crud_generator.generator.LambdaGraphQLQueryGenerator import LambdaGraphQLQueryGenerator
from django_graphene_crud_generator.generator.TokenBasedAuthenticationComponent import TokenBasedAuthenticationComponent
from django_graphene_crud_generator.types import GrapheneBodyFunction


# ##################################################
# MUTATION
# ##################################################


def create_simple_mutation_generator(
        class_name: str,
        description: Union[str, List[str]],
        arguments: Dict[str, TGrapheneArgument],
        return_value: TGrapheneWholeQueryReturnType,
        callable: GrapheneBodyFunction
) -> AbstractGraphQLMutationGenerator:
    s = LambdaGraphQLMutationGenerator(class_name, description, arguments, return_value, callable)
    return s


def create_simple_mutation(
        class_name: str,
        description: Union[str, List[str]],
        arguments: Dict[str, TGrapheneArgument],
        return_value: TGrapheneWholeQueryReturnType,
        callable: GrapheneBodyFunction,
        **kwargs
) -> TGrapheneMutation:
    s = create_simple_mutation_generator(class_name, description, arguments, return_value, callable)
    return s.generate(**kwargs)


def create_token_authenticated_mutation(
    class_name: str,
    description: Union[str, List[str]],
    arguments: Dict[str, TGrapheneArgument],
    return_value: TGrapheneWholeQueryReturnType,
    callable: GrapheneBodyFunction,
    token_name: str = None,
    permissions: List[str] = None,
) -> TGrapheneMutation:
    s = create_simple_mutation_generator(class_name, description, arguments, return_value, callable)
    s.register_component(TokenBasedAuthenticationComponent())
    if token_name is None:
        token_name = "token"
    if permissions is None:
        permissions = []
    return s.generate(
        token_name=token_name,
        permissions=permissions,
    )

# ##################################################
# QUERY
# ##################################################


def create_simple_query_generator(
        class_name: str,
        description: Union[str, List[str]],
        output_name: str,
        arguments: Dict[str, TGrapheneArgument],
        return_value: TGrapheneWholeQueryReturnType,
        callable: GrapheneBodyFunction
) -> AbstractGraphQLQueryGenerator:
    s = LambdaGraphQLQueryGenerator(class_name, description, arguments, output_name, return_value, callable)
    return s


def create_simple_query(
        class_name: str,
        description: Union[str, List[str]],
        output_name: str,
        arguments: Dict[str, TGrapheneArgument],
        return_value: TGrapheneWholeQueryReturnType,
        callable: GrapheneBodyFunction,
        **kwargs
) -> TGrapheneQuery:
    s = create_simple_query_generator(class_name, description, arguments, output_name, return_value, callable)
    return s.generate(**kwargs)


def create_token_authenticated_query(
    class_name: str,
    description: Union[str, List[str]],
    arguments: Dict[str, TGrapheneArgument],
    return_value: TGrapheneWholeQueryReturnType,
    callable: GrapheneBodyFunction,
    token_name: str = None,
    permissions: List[str] = None,
) -> TGrapheneQuery:
    s = create_simple_query_generator(class_name, description, arguments, return_value, callable)
    s.register_component(TokenBasedAuthenticationComponent())
    if token_name is None:
        token_name = "token"
    if permissions is None:
        permissions = []
    return s.generate(
        token_name=token_name,
        permissions=permissions,
    )
