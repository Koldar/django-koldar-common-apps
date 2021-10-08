import functools

import stringcase
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneWholeQueryReturnType

from django_graphene_crud_generator.IGraphQLEndpointComponent import IGraphQLEndpointComponent
from django_graphene_crud_generator.CrudBuildPhaseEnum import CrudBuildPhaseEnum
from django_graphene_crud_generator.crud_generator.AbstractGraphQLCrudComponent import AbstractGraphQLCrudComponent
from django_graphene_crud_generator.crud_generator.contexts import CRUDBuildContext, CRUDRuntimeContext
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext
from django_graphene_crud_generator.types import GrapheneGeneratorBodyFunction


from typing import Dict, Callable, List, Tuple

from django_koldar_utils.django_toolbox import auth_decorators
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneArgument

from django_graphene_crud_generator.crud_generator.contexts import CRUDBuildContext


class ReadQueryByInputtingMatcher(AbstractGraphQLCrudComponent):
    """
    We configure the graphql endpoint to require a nullable input representing the pattern a value compliant with all its non
    None value needs to have in order to be returned. If the input is None, we fetch all the elements.

    What you do with that pattern is no concern fo thix mixin
    """

    def _get_query_input_parameter_name(self, build_context: CRUDBuildContext) -> str:
        """
        Name of the parameter in create mutation that defines the element to add
        """
        return f"{stringcase.camelcase(build_context.django_type.__name__)}Match"

    def _generate_action_arguments(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, Dict[str, TGrapheneArgument]]:
        crud_build_context = self.crud_build_context(build_context)

        result = dict()
        input_name = self._get_query_input_parameter_name(crud_build_context)
        result[input_name] = GraphQLHelper.argument_nullable_input(
            input_type=crud_build_context.graphene_input_type,
            description="""a template that is used to retrieve elements from the system. We retrieve only the elements
                        that have the same non-null elements w.r.t this parameter. If the parameter is None we will
                        return all the elements in the system
            """)

        return "update", result


class AddCRUDRuntimeContextComponent(AbstractGraphQLCrudComponent):
    """
    Add to the runtime_context
    """

    def _graphql_body_function_decorator(self, runtime_context: GraphQLRuntimeContext):
        def decorator(generator_body):
            @functools.wraps(generator_body)
            def wrapper(*args, **kwargs):
                nonlocal self
                runtime_context.params["crud_runtime_context"] = CRUDRuntimeContext(
                    c=self.crud_build_context(runtime_context.build_context),
                    info=runtime_context.info,
                    graphql_class=runtime_context.root,
                    *runtime_context.args, **runtime_context.kwargs
                )
                return generator_body(*args, **kwargs)
            return wrapper
        return decorator


class FederatedNamesCrudComponent(AbstractGraphQLCrudComponent):
    """
    If you are developing a federation, the names within the federation needs to be unique.
    This namer enforces it. We assume the user has passed a parameters called "subgraph_name"
    during the init of the crud graphql generator
    """

    def subgraph_name(self, crud_build_context: CRUDBuildContext) -> str:
        return crud_build_context.params["subgraph_name"]

    def _generate_action_class_name(self, build_context: GraphQLBuildtimeContext) -> str:
        crud_build_context = self.crud_build_context(build_context)
        django_type = crud_build_context.django_type
        federation_action_class_name_mapper = dict()

        if crud_build_context.build_phase == CrudBuildPhaseEnum.CREATE:
            new_key = f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}Create{stringcase.pascalcase(django_type.__name__)}Item"
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.READ_SINGLE:
            new_key = f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}ReadSingle{stringcase.pascalcase(django_type.__name__)}Item"
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.READ_ALL:
            new_key = f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}ReadAll{stringcase.pascalcase(django_type.__name__)}Items"
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.UPDATE:
            new_key = f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}Update{stringcase.pascalcase(django_type.__name__)}Items"
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.DELETE:
            new_key = f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}Delete{stringcase.pascalcase(django_type.__name__)}Items"
        else:
            raise ValueError(f"invalid build phase {crud_build_context.build_phase}")

        federation_action_class_name_mapper[new_key] = build_context.action_class_name
        build_context.action_class_name = new_key
        build_context.set_data("federation_action_class_name_mapper", federation_action_class_name_mapper)
        return new_key

    def _get_query_output_name(self, build_context: GraphQLBuildtimeContext) -> str:
        crud_build_context = self.crud_build_context(build_context)
        previous_result = build_context.get_data("_get_query_output_name_result")
        return f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}{stringcase.pascalcase(previous_result)}"

    # TODO remove
    # def _generate_additional_class_names(self, class_name: str, build_context: GraphQLBuildtimeContext) -> str:
    #     crud_build_context = self.crud_build_context(build_context)
    #     return f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}{class_name}"
    #
    # def _generate_additional_class_return_type_names(self, original_class_name: str, return_value_name: str, build_context: GraphQLBuildtimeContext) -> str:
    #     crud_build_context = self.crud_build_context(build_context)
    #     return f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}{return_value_name}"

    def _generate_action_return_type(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, TGrapheneWholeQueryReturnType]:
        crud_build_context = self.crud_build_context(build_context)
        django_type = crud_build_context.django_type
        result = dict()
        federation_action_return_type_name_mapper = dict()
        if crud_build_context.build_phase == CrudBuildPhaseEnum.CREATE:
            for k, v in list(build_context.action_return_type.items()):
                new_key = f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}{stringcase.pascalcase(k)}"
                federation_action_return_type_name_mapper[new_key] = k
                result[new_key] = v
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.READ_SINGLE:
            for k, v in build_context.action_return_type.items():
                new_key = f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}{stringcase.pascalcase(k)}"
                federation_action_return_type_name_mapper[new_key] = k
                result[new_key] = v
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.READ_ALL:
            for k, v in build_context.action_return_type.items():
                new_key = f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}{stringcase.pascalcase(k)}"
                federation_action_return_type_name_mapper[new_key] = k
                result[new_key] = v
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.UPDATE:
            for k, v in build_context.action_return_type.items():
                new_key = f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}{stringcase.pascalcase(k)}"
                federation_action_return_type_name_mapper[new_key] = k
                result[new_key] = v
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.DELETE:
            for k, v in build_context.action_return_type.items():
                new_key = f"{stringcase.camelcase(self.subgraph_name(crud_build_context))}{stringcase.pascalcase(k)}"
                federation_action_return_type_name_mapper[new_key] = k
                result[new_key] = v
        else:
            raise ValueError(f"invalid build phase {crud_build_context.build_phase}")

        build_context.set_data("federation_action_return_type_name_mapper", federation_action_return_type_name_mapper)

        return "set", result


class StandardNamesComponent(AbstractGraphQLCrudComponent):
    """
    A simple implementation to generate the names of all the relevant graphql names and return values
    """

    def _generate_action_class_name(self, build_context: GraphQLBuildtimeContext) -> str:
        crud_build_context = self.crud_build_context(build_context)
        if crud_build_context.build_phase == CrudBuildPhaseEnum.CREATE:
            return f"create{stringcase.pascalcase(crud_build_context.django_type.__name__)}Item"
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.READ_SINGLE:
            return f"readSingle{stringcase.pascalcase(crud_build_context.django_type.__name__)}Item"
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.READ_ALL:
            return f"readAll{stringcase.pascalcase(crud_build_context.django_type.__name__)}Items"
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.UPDATE:
            return f"update{stringcase.pascalcase(crud_build_context.django_type.__name__)}Item"
        elif crud_build_context.build_phase == CrudBuildPhaseEnum.DELETE:
            return f"delete{stringcase.pascalcase(crud_build_context.django_type.__name__)}Item"
        else:
            raise ValueError(f"invalid build phase {crud_build_context.build_phase}")

    def _generate_action_return_type(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, TGrapheneWholeQueryReturnType]:
        return "update", dict()
