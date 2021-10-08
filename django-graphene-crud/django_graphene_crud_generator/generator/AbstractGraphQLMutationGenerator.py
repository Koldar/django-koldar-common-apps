import abc
import logging

import graphene
from koldar_utils.functions import logic_helpers
from django_koldar_utils.graphql_toolsbox import graphql_decorators

from django_graphene_crud_generator.generator.AbstractGraphQLEndpointGenerator import AbstractGraphQLEndpointGenerator
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext


LOG = logging.getLogger(__name__)


class AbstractGraphQLMutationGenerator(AbstractGraphQLEndpointGenerator, abc.ABC):
    """
    Generate a query via graphene and automatically registers it with graphql_subquery decorator
    """

    def _compute_graphene_class(self, build_context: GraphQLBuildtimeContext) -> type:
        assert build_context.action_class_name is not None, "mutation class name is none"
        assert all(map(lambda x: x is not None, build_context.action_arguments.keys())), f"argument of {build_context.action_class_name} are none"
        assert build_context.action_return_type is not None, "return type is None. This should not be possible"
        assert "mutate" not in build_context.action_return_type.keys(), f"mutate in return type of class {build_context.action_class_name}"
        assert all(
            map(lambda x: x is not None, build_context.action_return_type.keys())), f"some return value of {build_context.action_class_name} are None"
        assert build_context.action_description is not None, f"description of {build_context.action_class_name} is None"
        assert isinstance(build_context.action_arguments, dict), f"argument is not a dictionary"
        assert logic_helpers.implies(len(build_context.action_arguments) > 0, lambda: isinstance(list(build_context.action_arguments.keys())[0], str)), f"argument keys are not strings, but {type(list(build_context.action_arguments.keys())[0])}!"

        mutation_class_meta = type(
            "Arguments",
            (object,),
            build_context.action_arguments
        )

        # def mutate(root, info, *args, **kwargs) -> any:
        #     nonlocal build_context
        #     if root is None:
        #         root = mutation_class
        #     runtime_context = GraphQLRuntimeContext(build_context, root, info, *args, **kwargs)
        #     LOG.info(f"Computing result for graphql mutation {build_context.action_class_name}...")
        #     result = build_context.action_body(runtime_context, *args, **kwargs)
        #     return result
        #build_context.action_body = mutate

        LOG.info(f"Argument are {build_context.action_arguments}")
        LOG.info(f"Creating mutation={build_context.action_class_name}; arguments keys={','.join(build_context.action_arguments.keys())}; return={', '.join(build_context.action_return_type.keys())}")
        mutation_class = type(
            build_context.action_class_name,
            (graphene.Mutation,),
            {
                "Arguments": mutation_class_meta,
                "__doc__": build_context.action_description,
                **build_context.action_return_type,
                "mutate": build_context.action_body
            }
        )
        # Apply decorator to auto detect mutations
        mutation_class = graphql_decorators.graphql_submutation(mutation_class)

        return mutation_class