from typing import Dict, List, Optional, Callable

from django_koldar_utils.django_toolbox import auth_decorators
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneArgument, TGrapheneWholeQueryReturnType

from django_graphene_crud_generator.IGraphQLEndpointComponent import IGraphQLEndpointComponent
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext
from django_graphene_crud_generator.types import GrapheneGeneratorBodyFunction, GrapheneBodyFunction


class PermissionComponent(IGraphQLEndpointComponent):

    def permissions(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        return build_context.get_param("permissions")

    def _generate_action_description(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        perms = ' - \n'.join(self.permissions(build_context))
        return [
            f"""In order to use this endpoint, the user logger needs to have the following permissions:
             {perms}
            """
        ]

    def _graphql_body_function_decorator_native(self, runtime_context: GraphQLRuntimeContext) -> Optional[GrapheneBodyFunction]:
        return auth_decorators.graphql_ensure_user_has_permissions(perm=self.permissions(runtime_context.build_context))


