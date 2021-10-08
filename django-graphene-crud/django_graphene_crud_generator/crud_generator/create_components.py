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
from django_graphene_crud_generator.generator.contexts import GraphQLRuntimeContext, GraphQLBuildtimeContext
from django_graphene_crud_generator.types import GrapheneGeneratorBodyFunction

LOG = logging.getLogger(__name__)


class CreateMutationReturnAddedValueComponent(AbstractGraphQLCrudComponent):
    """
    The component will make so the return value of the mutation is true if we have added something to the database,
    false otherwise; alongside the value from the database
    """

    def _generate_action_return_type(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, TGrapheneWholeQueryReturnType]:
        result = dict()
        crud_build_context = self.crud_build_context(build_context)
        flag_name = self._get_mutation_success_ok_name(crud_build_context)
        return_name = self._get_mutation_success_return_name(crud_build_context)
        # first boolean, then object
        result[flag_name] = GraphQLHelper.return_ok()
        result[return_name] = GraphQLHelper.return_nullable(crud_build_context.graphene_type)
        return "set", result

    def _get_mutation_success_return_name(self, context: CRUDBuildContext) -> str:
        return stringcase.camelcase(context.django_type.__name__)

    def _get_mutation_success_ok_name(self, context: CRUDBuildContext) -> str:
        return "ok"

    def _graphql_body_function_decorator(self, runtime_context: GraphQLRuntimeContext):
        def decorator(generator_function):
            @functools.wraps(generator_function)
            def wrapper(*args, **kwargs):
                result = generator_function(*args, **kwargs)
                # result is something like dict(obj=item_in_db[0], added=False)
                obj, create_args = result["obj"]
                added = result["added"]
                return runtime_context.build_context.action_class(added, obj)
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


class CreateMutationByInputtingSingleInput(AbstractGraphQLCrudComponent):

    def _get_mutation_input_parameter_name(self, build_context: CRUDBuildContext) -> str:
        """
        Name of the parameter in create mutation that defines the element to add
        """
        return stringcase.camelcase(build_context.django_type.__name__)

    def _generate_action_arguments(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, Dict[str, TGrapheneArgument]]:
        crud_build_context = self.crud_build_context(build_context)

        result = dict()
        input_name = self._get_mutation_input_parameter_name(crud_build_context)
        result[input_name] = GraphQLHelper.argument_required_input(input_type=crud_build_context.graphene_input_type)

        return "update", result


class StandardCrudCreateMutation(AddCRUDContextComponentMixIn, AbstractCreateGraphQLMutationGenerator):
    """
    Represents the default create mutation generator that we will use in the implementation of ICrudGraphQLEndpointGenerator.

    Note that the mutation will always output a dictionary where "obj" key is an object (possibly just created) and
    "added" a flag which i set if the object has been added to the db. If you want to customize, consider adding components.

    In order to work, you still need to decide the arguments and the return value of the mutation. Use components to agument
    it or derive the class. It is indifferent
    """
    def _create_generate_mutation_instance_row_already_exists(self, mutation_class: type, item_in_db: models.Model,
                                                              runtime_context: GraphQLRuntimeContext) -> any:
        return dict(obj=(item_in_db, {}), added=False)

    def _create_generate_mutation_instance_row_added(self, mutation_class: type, result: any,
                                                     runtime_context: GraphQLRuntimeContext) -> any:
        return dict(obj=result, added=True)

    def get_django_type_involved(self, build_context: GraphQLBuildtimeContext) -> TDjangoModelType:
        return self.django_type(build_context)

    def _generate_action_description(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        return [
            "To detect if an object is already present in the database, we will use the uniquye fields of the model."
            "We will create just the primitive data of the entity, not the relationships"
        ]

    def _get_description_object_already_present_in_database(self, context: GraphQLBuildtimeContext) -> List[str]:
        return ["If the object requested is already present in the database, we do nothing"]

    def _get_fields_to_check(self, crud_runtime_context: CRUDRuntimeContext) -> List[str]:
        return list(
            map(lambda x: x.name, django_helpers.get_unique_field_names(crud_runtime_context.crud_build_context.django_type)))

    def _get_mutation_input_parameter_name(self, build_context: GraphQLBuildtimeContext) -> str:
        expected = stringcase.lowercase(self.django_type(build_context).__name__)
        for name, field in build_context.action_arguments.items():
            if expected in name and GraphQLHelper.is_representing_input_argument(field):
                return name
        else:
            raise ValueError(f"cannot identify the argument representing the object to add. Arguments are {', '.join(build_context.action_arguments.keys())}")

    def _check_if_object_exists(self, django_type: TDjangoModelType, runtime_context: GraphQLRuntimeContext) -> Tuple[
        bool, Optional[models.Model]]:
        crud_runtime_context = self.crud_runtime_context(runtime_context)
        input_name = self._get_mutation_input_parameter_name(runtime_context.build_context)
        input_dict = self._convert_input(runtime_context.kwargs[input_name])
        query_dict = dict()
        available_field = django_helpers.get_primitive_fields(django_type)

        for f in self._get_fields_to_check(crud_runtime_context):
            if f not in available_field:
                # the field in the django model is not available in the associated graphene input.
                # input is generated by the user, hence sometimes the user creates an input which do not have a field
                continue
            query_dict[f] = getattr(input_dict, f)

        LOG.info(f"Checking if exists a {django_type.__name__} object s.t. {query_dict}")
        result = list(django_type._default_manager.filter(**query_dict))
        if len(result) > 0:
            LOG.info(f"At least one Django model of type {django_type.__name__} exists!")
            return True, result
        else:
            LOG.info(f"No django model of type {django_type.__name__} exists")
            return False, None

    def _add_new_object_in_database(self, django_type: TDjangoModelType,
                                    runtime_context: CRUDRuntimeContext) -> any:
        """
        Adds a new object in the database. You are ensured that the object does not yet exist in the database

        :param django_type: type of the model to fetch
        :param info: graphql info value
        :param args: graphql args
        :param kwargs: graphql kwargs
        :return: anything you want. It should repersents the added row though
        """
        input_name = self._get_mutation_input_parameter_name(runtime_context.build_context)
        input_dict = runtime_context.kwargs[input_name]
        # create argumejnt and omits the None values
        create_args = {k: v for k, v in dict(input_dict).items() if v is not None}
        result = django_type._default_manager.create(**create_args)
        return result, create_args

    def _check_new_object_return_value(self, result: any, django_type: TDjangoModelType,
                                       runtime_context: CRUDRuntimeContext):
        value, create_args = result
        if value is None:
            raise GraphQLAppError(error_codes.CREATION_FAILED, object=django_type.__name__, values=create_args)
