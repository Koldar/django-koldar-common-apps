from typing import List

import stringcase
from django_koldar_utils.graphql_toolsbox.graphql_types import TDjangoModelType

from django_graphene_crud_generator.crud_generator.contexts import CRUDBuildContext, CRUDRuntimeContext
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext


class AddCRUDContextComponentMixIn:
    """
    Components using this class will be able to gain access to both CRUD build and runtime
    context
    """

    def crud_build_context(self, build_context: GraphQLBuildtimeContext) -> CRUDBuildContext:
        return build_context.get_param("crud_build_context")

    def crud_runtime_context(self, runtime_context: GraphQLRuntimeContext) -> CRUDRuntimeContext:
        return runtime_context.params["crud_runtime_context"]

    def django_type(self, build_context: GraphQLBuildtimeContext) -> TDjangoModelType:
        return self.crud_build_context(build_context).django_type


class CanXPermissionsGraphQLCrudGeneratorMixIn:
    """
    A mix in to support ICrudGraphQLGenerator implementations.

    This mixin configure the generator in such a way that it uses "can_X_Y" permissions,
    where X is either "create, view, update, delete" while Y is the snake case of a django model (e.g. foobar)
    """

    def _get_permissions_to_create(self, endpoint: str, context: CRUDBuildContext) -> List[str]:
        return [f"add_{stringcase.snakecase(context.django_type.__name__)}"]

    def _get_permissions_to_read_single(self, endpoint: str, context: CRUDBuildContext) -> List[str]:
        return [f"view_{stringcase.snakecase(context.django_type.__name__)}"]

    def _get_permissions_to_read_all(self, endpoint: str, context: CRUDBuildContext) -> List[str]:
        return [f"view_{stringcase.snakecase(context.django_type.__name__)}"]

    def _get_permissions_to_update(self, endpoint: str, context: CRUDBuildContext) -> List[str]:
        return [f"change_{stringcase.snakecase(context.django_type.__name__)}"]

    def _get_permissions_to_delete(self, endpoint: str, context: CRUDBuildContext) -> List[str]:
        return [f"delete_{stringcase.snakecase(context.django_type.__name__)}"]