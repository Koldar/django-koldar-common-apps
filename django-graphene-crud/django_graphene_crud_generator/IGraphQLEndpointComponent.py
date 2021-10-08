import abc
from typing import Dict, List, Callable, Optional, Tuple

from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneArgument, TGrapheneWholeQueryReturnType

from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext
from django_graphene_crud_generator.types import GrapheneGeneratorBodyFunction, GrapheneBodyFunction


class IGraphQLEndpointComponent(abc.ABC):

    def _generate_action_arguments(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, Dict[str, TGrapheneArgument]]:
        """
        Use "dict()" if you don't want to add anything to the arguments
        :return: list of parameters the class to generate will have. These are the graphql parameter. The first item
            in the pair is a string that can be one of the following:
             - update: we will add these arguments to the currently present arguments;
             - subtract: we will remove the keys of this dictioanry from the currently present arguments;
             - set: we will discard completely the previous arguments and overrides them with these ones
        """
        return "update", dict()

    def _generate_action_description(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        """
        Use "[]" if you don't want to add anything to the description

        :return: __doc__ of the class representing this action. Eac element in the list repersents a documentation
        paragraph. Paragraphs are then join together with "\n"
        """
        return []

    def _generate_action_return_type(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, TGrapheneWholeQueryReturnType]:
        """
        Use "dict()" if you don't want to alter the return type in any way
        :return: list of parameters the class to generate will have. These are the graphql parameter. The first item
            in the pair is a string that can be one of the following:
             - update: we will add these return values to the currently present arguments;
             - subtract: we will remove the keys of this dictioanry from the currently present return values;
             - set: we will discard completely the previous return values and overrides them with these ones
        """
        return "update", dict()

    def _generate_action_class_name(self, build_context: GraphQLBuildtimeContext) -> str:
        """
        Use "build_context.action_class_name" if you don't want to alter the class name
        :return: name of the class representing this action
        """
        return build_context.action_class_name

    def _graphql_body_function_decorator_native(self, runtime_context: GraphQLRuntimeContext) -> Optional[GrapheneBodyFunction]:
        """
        A function that agument the standard body function of the endpoint.
        Use "None" if you don't want to alter the function in any way

        :return: a decorated function, or None if you don't need one. The decorator function accepts in input
            a function A whose signature signature is:
             - type, info, *args, **kwargs -> any

        """
        return None

    def _graphql_body_function_decorator(self, runtime_context: GraphQLRuntimeContext) -> Optional[GrapheneGeneratorBodyFunction]:
        """
        A function that agument the standard body function of the endpoint.
        Use "None" if you don't want to alter the function in any way

        :param body_function: body function to call. parameters are:
         - grpahql runtime
         - graphql args
         - graphql kwargs
         - the grpahql endpioint result
        :return: a decorated function, or None if you don't need one. The decorator function accepts in input
            a function A whose signature signature is:
             - GraphQLRuntimeContext, *args, **kwargs -> any
        """
        return None