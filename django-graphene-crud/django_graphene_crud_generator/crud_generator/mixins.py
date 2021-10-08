from typing import List, Dict

import graphene
import stringcase
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
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

    def _convert_input(self, input: graphene.InputObjectType) -> Dict[str, any]:
        """
        Convert an input passed from graphene into a dictionary. If the inoptu is null (it might happen) return an
        empty dictionary
        :param input: input to convert
        :return: converted dictionary
        """
        if input is None:
            return dict()
        if isinstance(input, dict):
            # before returning we will need to filter out None value
            d = dict()
            for k, v in input.items():
                if v is not None:
                    d[k] = v
            return d
        d = dict()
        for k, v in dict(input).items():
            if v is None:
                continue
            if GraphQLHelper.is_representing_input_argument(v):
                d[k] = self._convert_input(v)
            else:
                d[k] = v
        return d


class CanXPermissionsGraphQLCrudGeneratorMixIn:
    """
    A mix in to support AbstractCrudGraphQLGenerator implementations.

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