from typing import Dict, List, Callable, Union, Tuple

from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneArgument, TGrapheneWholeQueryReturnType

from django_graphene_crud_generator.generator.AbstractGraphQLMutationGenerator import AbstractGraphQLMutationGenerator
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext


class LambdaGraphQLMutationGenerator(AbstractGraphQLMutationGenerator):
    """
    A mutation generator that uses fields passed during initialization in order to generate the mutation class.
    Useful if you don't need to customize the behavior in any way
    """

    def __init__(self, class_name: str,
        description: Union[str, List[str]],
        arguments: Dict[str, TGrapheneArgument],
        return_value: TGrapheneWholeQueryReturnType,
        callable: Callable[[any, any, List[any], Dict[str, any]], any]):

        self.class_name = class_name
        self.description = description
        self.arguments = arguments
        self.return_value = return_value
        self.callable = callable

    def _generate_action_class_name(self, build_context: GraphQLBuildtimeContext) -> str:
        return self.class_name

    def _generate_action_description(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        if isinstance(self.description, str):
            return [self.description]
        return self.description

    def _generate_action_arguments(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, Dict[str, TGrapheneArgument]]:
        return "set", self.arguments

    def _generate_action_return_type(self, build_context: GraphQLBuildtimeContext) -> TGrapheneWholeQueryReturnType:
        return self.return_value

    def graphql_body_function(self, runtime_context: GraphQLRuntimeContext, *args,
                              **kwargs) -> TGrapheneWholeQueryReturnType:
        return self.callable(runtime_context.root, runtime_context.info, *runtime_context.args, **runtime_context.kwargs)