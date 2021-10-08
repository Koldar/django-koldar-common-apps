from typing import Dict, List, Tuple

from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneArgument, TGrapheneWholeQueryReturnType

from django_graphene_crud_generator.IGraphQLEndpointComponent import IGraphQLEndpointComponent
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext
from django_graphene_crud_generator.types import GrapheneGeneratorBodyFunction


class TokenBasedAuthenticationComponent(IGraphQLEndpointComponent):

    def token_name(self, build_context: GraphQLBuildtimeContext) -> str:
        return build_context.get_param("token_name")

    def _generate_action_description(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        return [
            f"""In order to use this endpoint, you ar required to pass a \"{self.token_name(build_context)}\" as argument which is
            a compliant authentication token.
            """
        ]

    def _generate_action_arguments(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, Dict[str, TGrapheneArgument]]:
        return "update", {
            self.token_name(build_context): GraphQLHelper.argument_jwt_token()
        }
