import functools
import logging
from typing import Dict, Tuple, Optional, List

import graphene
import stringcase
from django.db import models
from django_koldar_utils.django_toolbox import django_helpers
from django_koldar_utils.graphql_toolsbox import error_codes
from django_koldar_utils.graphql_toolsbox.GraphQLAppError import GraphQLAppError
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneWholeQueryReturnType, TGrapheneArgument, \
    TDjangoModelType

from django_graphene_crud_generator.IGraphQLEndpointComponent import IGraphQLEndpointComponent
from django_graphene_crud_generator.crud_generator.AbstractGraphQLCrudComponent import AbstractGraphQLCrudComponent, \
    AddCRUDContextComponentMixIn
from django_graphene_crud_generator.crud_generator.contexts import CRUDBuildContext, CRUDRuntimeContext
from django_graphene_crud_generator.generator.AbstractCreateGraphQLMutationGenerator import \
    AbstractCreateGraphQLMutationGenerator
from django_graphene_crud_generator.generator.AbstractGraphQLMutationGenerator import AbstractGraphQLMutationGenerator
from django_graphene_crud_generator.generator.AbstractGraphQLEndpointGenerator import AbstractGraphQLEndpointGenerator
from django_graphene_crud_generator.generator.AbstractUpdateGraphQLMutationGenerator import \
    AbstractUpdateGraphQLMutationGenerator
from django_graphene_crud_generator.generator.contexts import GraphQLRuntimeContext, GraphQLBuildtimeContext
from django_graphene_crud_generator.types import GrapheneGeneratorBodyFunction

LOG = logging.getLogger(__name__)


class UpdateMutationReturnUpdatedValueComponent(AbstractGraphQLCrudComponent):
    """
    The component will make so the return value of the mutation is true if we have added something to the database,
    false otherwise; alongside the value from the database
    """

    def _generate_action_return_type(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, TGrapheneWholeQueryReturnType]:
        result = dict()
        crud_build_context = self.crud_build_context(build_context)
        count_name = self._get_mutation_success_count_name(crud_build_context)
        return_name = self._get_mutation_success_return_name(crud_build_context)
        # first boolean, then object
        result[count_name] = GraphQLHelper.returns_nonnull_int(description=f"Number of elements updated by the call")
        result[return_name] = GraphQLHelper.returns_nonnull_list(crud_build_context.graphene_type)
        return "update", result

    def _get_mutation_success_return_name(self, context: CRUDBuildContext) -> str:
        return stringcase.camelcase(context.django_type.__name__)

    def _get_mutation_success_count_name(self, context: CRUDBuildContext) -> str:
        return "count"

    def _graphql_body_function_decorator(self, runtime_context: GraphQLRuntimeContext):
        def decorator(generator_function):
            @functools.wraps(generator_function)
            def wrapper(*args, **kwargs):
                result = generator_function(*args, **kwargs)
                # result is something like dict(count=1, items=[x])
                items = result["items"]
                count = result["count"]
                return runtime_context.build_context.action_class(count, items)
            return wrapper
        return decorator


class CreateMutationReturnTrueComponent(AbstractGraphQLCrudComponent):
    """
    The component will make so the return value of the mutation is true if we have added something to the database, false otherwise
    """

    def _generate_action_return_type(self, build_context: GraphQLBuildtimeContext) -> TGrapheneWholeQueryReturnType:
        result = dict()
        crud_build_context = self.crud_build_context(build_context)
        flag_name = self._get_mutation_success_ok_name(crud_build_context)
        # first boolean, then object
        result[flag_name] = GraphQLHelper.return_ok()
        return result

    def _get_mutation_success_ok_name(self, context: CRUDBuildContext) -> str:
        return "ok"

    def _graphql_body_function_decorator(self, runtime_context: GraphQLRuntimeContext):
        def decorator(generator_body):
            @functools.wraps(generator_body)
            def wrapper(*args, **kwargs):
                result = generator_body(*args, **kwargs)
                # result is something like dict(obj=item_in_db[0], added=False)
                added = result["added"]
                return runtime_context.build_context.action_class(added)
            return wrapper
        return decorator


class UpdateMutationByInputtingTwoInput(AbstractGraphQLCrudComponent):
    """
    The update will have 2 input parameters: one containing "match" word representing the set of rows that we need to update
    while the other containing the word "new" representing the revised data we want the object to have. We can use it
    in udpate mutation to both identify the object to update and the new values it needs to have.

    """

    def _get_mutation_match_input_parameter_name(self, build_context: CRUDBuildContext) -> str:
        """
        Name of the parameter in create mutation that defines the element to add
        """
        return f"{stringcase.camelcase(build_context.django_type.__name__)}Match"

    def _get_mutation_new_input_parameter_name(self, build_context: CRUDBuildContext) -> str:
        """
        Name of the parameter in create mutation that defines the element to add
        """
        return f"new{stringcase.pascalcase(build_context.django_type.__name__)}"

    def _generate_action_arguments(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, Dict[str, TGrapheneArgument]]:
        crud_build_context = self.crud_build_context(build_context)

        result = dict()
        match_name = self._get_mutation_match_input_parameter_name(crud_build_context)
        new_name = self._get_mutation_new_input_parameter_name(crud_build_context)
        result[match_name] = GraphQLHelper.argument_required_input(input_type=crud_build_context.graphene_input_type)
        result[new_name] = GraphQLHelper.argument_required_input(input_type=crud_build_context.graphene_input_type)

        return "update", result


class StandardCrudUpdateMutation(AddCRUDContextComponentMixIn, AbstractUpdateGraphQLMutationGenerator):
    """
    Represents the default create mutation generator that we will use in the implementation of ICrudGraphQLEndpointGenerator.
    We assume we have 2 inputs: one representing the row to alter (e.g., specifying an id) the other representing the
    revised data

    Note that the mutation will always output a dictionary where "obj" key is an object (possibly just created) and
    "added" a flag which i set if the object has been added to the db. If you want to customize, consider adding components.

    In order to work, you still need to decide the arguments and the return value of the mutation. Use components to agument
    it or derive the class. It is indifferent.

    If the filter used to determine which element we need to update is empty, we have a fail safe mechanism that return
    zero items to update instead of all of them
    """

    def get_django_type_involved(self, build_context: GraphQLBuildtimeContext) -> TDjangoModelType:
        return self.django_type(build_context)

    def _get_description_object_is_not_present_in_database(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        return [
            "If the object is not present in the database, we do nothing"
        ]

    def _get_mutation_input_representing_data_to_revise_parameter_name(self, build_context: GraphQLBuildtimeContext) -> str:
        expected = stringcase.lowercase(self.django_type(build_context).__name__)
        for name, field in build_context.action_arguments.items():
            if expected not in name.lower():
                continue
            if not GraphQLHelper.is_representing_input_argument(field):
                continue
            if "match" not in name.lower():
                continue
            return name
        else:
            raise ValueError(f"cannot identify the argument representing the objects we need to update. Arguments are {', '.join(build_context.action_arguments.keys())}")

    def _get_mutation_input_representing_revised_data_parameter_name(self, build_context: GraphQLBuildtimeContext) -> str:
        expected = stringcase.lowercase(self.django_type(build_context).__name__)
        for name, field in build_context.action_arguments.items():
            if expected not in name.lower():
                continue
            if not GraphQLHelper.is_representing_input_argument(field):
                continue
            if "new" not in name.lower():
                continue
            return name
        else:
            raise ValueError(
                f"cannot identify the argument representing the object holding the new data to set. Arguments are {', '.join(build_context.action_arguments.keys())}")

    def _check_if_object_exists(self, django_type: TDjangoModelType, runtime_context: GraphQLRuntimeContext) -> Tuple[
        bool, Optional[models.Model]]:
        crud_runtime_context = self.crud_runtime_context(runtime_context)
        input_name = self._get_mutation_input_representing_data_to_revise_parameter_name(runtime_context.build_context)
        match_input = runtime_context.kwargs[input_name]
        input_dict = self._convert_input(match_input)
        query_dict = dict()
        available_field = list(map(lambda x: x.name, django_helpers.get_primitive_fields(django_type)))
        fields_to_check = list(self._get_fields_to_check(crud_runtime_context))
        for f in fields_to_check:
            if f not in available_field:
                # the field in the django model is not available in the associated graphene input.
                # input is generated by the user, hence sometimes the user creates an input which do not have a field
                LOG.info(f"""We were trying to use field \"{f}\" t fetch the elements to update in this endpoint. 
                However, the element chosen is not among the following one: 
                {', '.join(available_field)}. Ignore him""")
                continue
            if f not in input_dict:
                LOG.info(f"field {f} has not been passed by the user. Skip it")
                continue
            query_dict[f] = getattr(match_input, f)

        LOG.info(f"Checking if exists a {django_type.__name__} object s.t. {query_dict}")
        if len(query_dict) == 0:
            LOG.warning(f"""The query used to fetch all the items to update is empty. Rather than letting the user
                to update all the fields we force the query to return no entries!""")
            result = []
        else:
            result = list(django_type._default_manager.filter(**query_dict))

        if len(result) > 0:
            LOG.info(f"At least one Django model of type {django_type.__name__} exists!")
            return True, result
        else:
            LOG.info(f"No django model of type {django_type.__name__} exists")
            return False, None

    def _update_object_in_database(self, django_type: TDjangoModelType, items_in_db: any,
                                   runtime_context: GraphQLRuntimeContext) -> any:
        revised_data_name = self._get_mutation_input_representing_revised_data_parameter_name(runtime_context.build_context)
        revised_data = runtime_context.kwargs[revised_data_name]
        result = []
        for row_to_change in items_in_db:
            for new_data_name, new_data_value in revised_data.items():
                if new_data_value is None:
                    continue
                setattr(row_to_change, new_data_name, new_data_value)
            row_to_change.save()
            result.append(row_to_change)
        return result


    def _check_update_object_return_value(self, result: any, django_type: TDjangoModelType,
                                          runtime_context: GraphQLRuntimeContext):
        pass

    def _update_generate_mutation_instance_does_not_exists(self, mutation_class: type,
                                                           runtime_context: GraphQLRuntimeContext) -> any:
        return dict(count=0, items=[])

    def _update_generate_mutation_instance_row_updated(self, mutation_class: type, result: any,
                                                       runtime_context: GraphQLRuntimeContext) -> any:
        return dict(count=len(result), items=list(result))

    def _get_fields_to_check(self, crud_runtime_context: CRUDRuntimeContext) -> List[str]:
        return list(
            map(lambda x: x.name, django_helpers.get_unique_field_names(crud_runtime_context.crud_build_context.django_type)))
