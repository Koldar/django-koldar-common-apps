import abc
from typing import List, Dict, Callable, Tuple

from django.db.models import QuerySet
from django_koldar_utils.django_toolbox import auth_decorators
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneReturnType, TGrapheneArgument

from django_graphene_crud_generator.AbstractCrudGraphQLGenerator import AbstractCrudGraphQLGenerator
from django_graphene_crud_generator.IGraphQLEndpointComponent import IGraphQLEndpointComponent
from django_graphene_crud_generator.crud_generator.contexts import CRUDBuildContext
from django_graphene_crud_generator.crud_generator.mixins import CanXPermissionsGraphQLCrudGeneratorMixIn
from django_graphene_crud_generator.generator.AbstractGraphQLMutationGenerator import AbstractGraphQLMutationGenerator
from django_graphene_crud_generator.generator.AbstractGraphQLQueryGenerator import AbstractGraphQLQueryGenerator
from django_graphene_crud_generator.generator.AbstractGraphQLEndpointGenerator import ComponentPriorityEnum
from django_graphene_crud_generator.generator.PermissionsComponent import PermissionComponent
from django_graphene_crud_generator.generator.TokenBasedAuthenticationComponent import TokenBasedAuthenticationComponent

from django_graphene_crud_generator.crud_generator import shared_components, create_components, read_components, \
    delete_components, update_components


class StandardFederatedTokenBasedCrudGenerator(CanXPermissionsGraphQLCrudGeneratorMixIn, AbstractCrudGraphQLGenerator):
    """
    Use this class when you want to generate crud operation tthat fully support graphql federations.
    """

    def __init__(self):
        super().__init__()

    def _get_create_graphql_generators(self, crud_build_context: CRUDBuildContext) -> Dict[str, AbstractGraphQLMutationGenerator]:
        return dict(
            default=create_components.StandardCrudCreateMutation()
        )

    def _get_read_single_graphql_generators(self, crud_build_context: CRUDBuildContext) -> Dict[
        str, AbstractGraphQLQueryGenerator]:
        return dict(
            default=read_components.StandardCrudReadQuery()
        )

    def _get_read_all_graphql_generators(self, crud_build_context: CRUDBuildContext) -> Dict[
        str, AbstractGraphQLQueryGenerator]:
        return dict(
            default=read_components.StandardCrudReadQuery()
        )

    def _get_update_graphql_generators(self, crud_build_context: CRUDBuildContext) -> Dict[str, AbstractGraphQLMutationGenerator]:
        return dict(
            default=update_components.StandardCrudUpdateMutation()
        )

    def _get_delete_graphql_generators(self, crud_build_context: CRUDBuildContext) -> Dict[str, AbstractGraphQLMutationGenerator]:
        return dict(
            default=delete_components.StandardCrudDeleteMutation()
        )

    def _get_common_components(self, build_context: CRUDBuildContext) -> List[Tuple[int, IGraphQLEndpointComponent]]:
        result = super()._get_common_components(build_context)
        result.extend([
            (int(ComponentPriorityEnum.HIGH_02), TokenBasedAuthenticationComponent()),
            (int(ComponentPriorityEnum.LOW_09), shared_components.FederatedNamesCrudComponent()), # ensure it occurs at the end of every registration
            (int(ComponentPriorityEnum.HIGH_01), PermissionComponent()),
        ])
        return result

    def _get_create_components(self, build_context: CRUDBuildContext) -> List[Tuple[int, IGraphQLEndpointComponent]]:
        return [
            (int(ComponentPriorityEnum.NORMAL), create_components.CreateMutationReturnAddedValueComponent()),
            (int(ComponentPriorityEnum.NORMAL), create_components.CreateMutationByInputtingSingleInput()),
        ]

    def _get_read_single_components(self, build_context: CRUDBuildContext) -> List[Tuple[int, IGraphQLEndpointComponent]]:
        return [
            (int(ComponentPriorityEnum.NORMAL), read_components.ReadQueryReturnSingleElement()),
            (int(ComponentPriorityEnum.NORMAL), shared_components.ReadQueryByInputtingMatcher()),
        ]

    def _get_read_all_components(self, build_context: CRUDBuildContext) -> List[Tuple[int, IGraphQLEndpointComponent]]:
        return [
            (int(ComponentPriorityEnum.NORMAL), read_components.ReadQueryReturnElementListWithCount()),
            (int(ComponentPriorityEnum.NORMAL), shared_components.ReadQueryByInputtingMatcher()),
        ]

    def _get_update_components(self, build_context: CRUDBuildContext) -> List[Tuple[int, IGraphQLEndpointComponent]]:
        return [
            (int(ComponentPriorityEnum.NORMAL), update_components.UpdateMutationByInputtingTwoInput()),
            (int(ComponentPriorityEnum.NORMAL), update_components.UpdateMutationReturnUpdatedValueComponent()),
        ]

    def _get_delete_components(self, build_context: CRUDBuildContext) -> List[Tuple[int, IGraphQLEndpointComponent]]:
        return [
            (int(ComponentPriorityEnum.NORMAL), delete_components.DeleteQueryReturnElementListWithCount()),
            (int(ComponentPriorityEnum.NORMAL), shared_components.ReadQueryByInputtingMatcher()),
        ]


class StandardSimpleTokenBasedCrudGenerator(StandardFederatedTokenBasedCrudGenerator):
    """
    Use this class when you want to generate crud operation whose names are not cluttered with federation namespaces.
    However the schema generated will likely not be federation compatible.
    """

    def _get_common_components(self, build_context: CRUDBuildContext) -> List[Tuple[int, IGraphQLEndpointComponent]]:
        result = super()._get_common_components(build_context)
        result.extend([
            (int(ComponentPriorityEnum.HIGH_02), TokenBasedAuthenticationComponent()),
            (int(ComponentPriorityEnum.HIGH_09), shared_components.StandardNamesComponent()),
            (int(ComponentPriorityEnum.HIGH_01), PermissionComponent()),
        ])
        return result
