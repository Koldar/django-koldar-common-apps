import abc
import functools
from typing import Dict, Tuple, Optional, List

import graphene
import stringcase
from django.db import models
from django.db.models import QuerySet
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
from django_graphene_crud_generator.generator.AbstractReadGraphQLQueryGenerator import \
    AbstractReadGraphQLQueryGenerator, AbstractReadAllReturnAllQuery
from django_graphene_crud_generator.generator.AbstractGraphQLEndpointGenerator import AbstractGraphQLEndpointGenerator
from django_graphene_crud_generator.generator.contexts import GraphQLRuntimeContext, GraphQLBuildtimeContext
from django_graphene_crud_generator.types import GrapheneGeneratorBodyFunction


class ReadQueryReturnSingleElement(AbstractGraphQLCrudComponent):
    """
    The component will make so the return value of the read single mutation is indeed a single element or,
    at most, None
    """

    def _generate_action_return_type(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, TGrapheneWholeQueryReturnType]:
        result = dict()
        crud_build_context = self.crud_build_context(build_context)
        return_name = self._get_query_success_return_name(crud_build_context)
        # first boolean, then object
        result[return_name] = GraphQLHelper.return_nullable(crud_build_context.graphene_type, description="Element fetched from the system, or None if it could not be found")
        return "update", result

    def _get_query_success_return_name(self, context: CRUDBuildContext) -> str:
        return stringcase.camelcase(context.django_type.__name__)

    def _get_query_output_name(self, build_context: GraphQLBuildtimeContext) -> str:
        crud_build_context = self.crud_build_context(build_context)
        django_type = crud_build_context.django_type
        return f"getSingle{stringcase.pascalcase(django_type.__name__)}"

    def _get_return_value_temp_type_name(self, build_context: GraphQLBuildtimeContext) -> str:
        crud_build_context = self.crud_build_context(build_context)
        django_type = crud_build_context.django_type
        return f"{stringcase.pascalcase(django_type.__name__)}CallResult"

    def _graphql_body_function_decorator(self, runtime_context: GraphQLRuntimeContext):
        def decorator(generator_function):
            @functools.wraps(generator_function)
            def wrapper(*args, **kwargs):
                result = generator_function(*args, **kwargs)
                count = result["count"]
                items = result["items"]
                if items is None or len(items) == 0:
                    items = None
                else:
                    # we assume we have already check thhat items is a at most 1 element long. We pick the firs one
                    items = list(items)[0]
                # result is something like dict(count=3, items=[a,b,c])
                # the single read query return an actual grpahene type repersenting the django type, so we don't even
                # need to create an instance fo action class
                return items
            return wrapper
        return decorator


class ReadQueryReturnElementListWithCount(AbstractGraphQLCrudComponent):
    """
    The component will make so the return value of the read query is always a (possibly empty) list
    """

    def _generate_action_return_type(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, TGrapheneWholeQueryReturnType]:
        result = dict()
        crud_build_context = self.crud_build_context(build_context)
        list_name = self._get_query_list_name(crud_build_context)
        count_name = self._get_query_count_name(crud_build_context)
        # first boolean, then object
        result[count_name] = GraphQLHelper.returns_nonnull_int(description="Number of elements in the list")
        result[list_name] = GraphQLHelper.returns_nonnull_list(crud_build_context.graphene_type, description="Elements fetched from the system")
        return "set", result

    def _get_query_output_name(self, build_context: GraphQLBuildtimeContext) -> str:
        crud_build_context = self.crud_build_context(build_context)
        django_type = crud_build_context.django_type
        return f"getAll{stringcase.pascalcase(django_type.__name__)}"

    def _get_return_value_temp_type_name(self, build_context: GraphQLBuildtimeContext) -> str:
        crud_build_context = self.crud_build_context(build_context)
        django_type = crud_build_context.django_type
        return f"{stringcase.pascalcase(django_type.__name__)}CallResult"

    def _get_query_count_name(self, context: CRUDBuildContext) -> str:
        return f"{stringcase.camelcase(context.django_type.__name__)}Count"

    def _get_query_list_name(self, context: CRUDBuildContext) -> str:
        return f"{stringcase.camelcase(context.django_type.__name__)}Items"

    def _graphql_body_function_decorator(self, runtime_context: GraphQLRuntimeContext):
        def decorator(generator_function):
            @functools.wraps(generator_function)
            def wrapper(*args, **kwargs):
                result = generator_function(*args, **kwargs)
                count = result["count"]
                items = result["items"]
                # result is something like dict(count=3, items=[a,b,c])
                if items is None:
                    # it should not be None, but just in case I added this control
                    items = []
                # if the user wants to output multiple values from this query, we need to return a dictioanary,
                # which in graphene is transalted into a temp class.
                # such class is available at build_context.get_data("query_temp_class")
                if runtime_context.build_context.has_data("query_temp_class"):
                    query_temp_class = runtime_context.build_context.get_data("query_temp_class")
                    tmp_instance = query_temp_class(count, items)
                    result = runtime_context.build_context.action_class(tmp_instance)
                    return result
                else:
                    return runtime_context.build_context.action_class(count, items)
            return wrapper
        return decorator


class AbstractCrudReadQuery(AddCRUDContextComponentMixIn, AbstractReadAllReturnAllQuery):
    """
    Represents the default create mutation generator that we will use in the implementation of ICrudGraphQLEndpointGenerator.

    Note that the mutation will always output a dictionary where "obj" key is an object (possibly just created) and
    "added" a flag which i set if the object has been added to the db. If you want to customize, consider adding components.

    In order to work, you still need to decide the arguments and the return value of the mutation. Use components to agument
    it or derive the class. It is indifferent
    """

    def _get_query_output_name(self, build_context: GraphQLBuildtimeContext) -> str:
        return self.call_component_method_with_result_store("_get_query_output_name", build_context, kwargs=dict(build_context=build_context))

    def _get_return_value_temp_type_name(self, build_context: GraphQLBuildtimeContext) -> str:
        return self.call_component_method("_get_return_value_temp_type_name", kwargs=dict(build_context=build_context))

    def _get_input_name(self, runtime_context: GraphQLRuntimeContext) -> str:
        build_context = runtime_context.build_context
        expected = stringcase.lowercase(self.django_type(build_context).__name__)
        for name, field in build_context.action_arguments.items():
            if expected in name and GraphQLHelper.is_representing_input_argument(field):
                return name
        else:
            raise ValueError(
                f"cannot identify the argument representing the object to add. Arguments are {', '.join(build_context.action_arguments.keys())}")

    @abc.abstractmethod
    def _get_compliant_instances(self, qs: QuerySet, main_criterion: Dict[str, any], runtime_context: GraphQLRuntimeContext) -> QuerySet:
        """
        This is the function that actually generates the sequence of items to return from the query
        :param qs: a query set generated by polling the all() method of the django type involved
        :param main_criterion: criterion used by fetching the graphql input parameter from _get_input_name
        :param runtime_context: graphql runtime context
        :return: query set that can be used to return by graphql
        """
        pass

    def _get_objects(self, django_type: TDjangoModelType, runtime_context: GraphQLRuntimeContext) -> Tuple[List[models.Model], Optional[any]]:
        input_name = self._get_input_name(runtime_context)

        # ok, fetch all the values that are compliant with this match
        qs = django_type._default_manager.all()
        output = self._get_compliant_instances(qs, runtime_context.kwargs[input_name], runtime_context)

        return output, runtime_context.get_input(input_name)

    def get_django_type_involved(self, build_context: GraphQLBuildtimeContext) -> TDjangoModelType:
        return self.django_type(build_context)


class StandardCrudReadQuery(AbstractCrudReadQuery):

    def _get_compliant_instances(self, qs: QuerySet, main_criterion: Dict[str, any],
                                 runtime_context: GraphQLRuntimeContext) -> QuerySet:
        # we assume main_criterion is a graphql input. We need to convert it to a dictionary, buyt we first need
        # to filter out None resuts
        d = self._convert_input(main_criterion)

        return qs.filter(**d)
