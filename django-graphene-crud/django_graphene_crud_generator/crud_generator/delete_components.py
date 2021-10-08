import functools
import logging
from typing import Tuple, Optional, List

import stringcase
from django.db import models
from django_koldar_utils.django_toolbox import django_helpers
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.graphql_types import TDjangoModelType, TGrapheneWholeQueryReturnType

from django_graphene_crud_generator.crud_generator.AbstractGraphQLCrudComponent import AbstractGraphQLCrudComponent
from django_graphene_crud_generator.crud_generator.contexts import CRUDRuntimeContext, CRUDBuildContext
from django_graphene_crud_generator.crud_generator.mixins import AddCRUDContextComponentMixIn
from django_graphene_crud_generator.crud_generator.shared_components import ReadQueryByInputtingMatcher
from django_graphene_crud_generator.generator.AbstractDeleteGraphQLMutationGenerator import \
    AbstractDeleteGraphQLMutationGenerator
from django_graphene_crud_generator.generator.contexts import GraphQLRuntimeContext, GraphQLBuildtimeContext

LOG = logging.getLogger(__name__)


class DeleteQueryReturnElementListWithCount(AbstractGraphQLCrudComponent):
    """
    The component will make so the return value of the read query is always a (possibly empty) list
    """

    def _generate_action_return_type(self, build_context: GraphQLBuildtimeContext) -> Tuple[str, TGrapheneWholeQueryReturnType]:
        result = dict()
        crud_build_context = self.crud_build_context(build_context)
        list_name = self._get_query_list_name(crud_build_context)
        count_name = self._get_query_count_name(crud_build_context)
        # first boolean, then object
        result[count_name] = GraphQLHelper.returns_nonnull_int(description="Number of elements that have been deleted")
        result[list_name] = GraphQLHelper.returns_nonnull_list(crud_build_context.graphene_type, description="Elements fetched from the system that now are deleted")
        return "update", result

    def _get_query_output_name(self, build_context: GraphQLBuildtimeContext) -> str:
        crud_build_context = self.crud_build_context(build_context)
        django_type = crud_build_context.django_type
        return f"deleteAll{stringcase.pascalcase(django_type.__name__)}"

    # def _get_return_value_temp_type_name(self, build_context: GraphQLBuildtimeContext) -> str:
    #     crud_build_context = self.crud_build_context(build_context)
    #     django_type = crud_build_context.django_type
    #     return f"{stringcase.pascalcase(django_type.__name__)}CallResult"

    def _get_query_count_name(self, context: CRUDBuildContext) -> str:
        return f"{stringcase.camelcase(context.django_type.__name__)}Count"

    def _get_query_list_name(self, context: CRUDBuildContext) -> str:
        return f"{stringcase.camelcase(context.django_type.__name__)}Items"

    def _graphql_body_function_decorator(self, runtime_context: GraphQLRuntimeContext):
        def decorator(generator_function):
            @functools.wraps(generator_function)
            def wrapper(*args, **kwargs):
                result = generator_function(*args, **kwargs)
                LOG.debug(f"delete crud generated data {result}")
                count = result["count"]
                items = result["items"]
                # result is something like dict(count=3, items=[a,b,c])
                if items is None:
                    # it should not be None, but just in case I added this control
                    items = []
                return runtime_context.build_context.action_class(count, items)
            return wrapper
        return decorator


class StandardCrudDeleteMutation(AddCRUDContextComponentMixIn, AbstractDeleteGraphQLMutationGenerator):
    """
    This delete mutation will use a matcher that can be used to delete multiple rows at once.
    It then return the count and the items that have been deleted. Note that by "deleted" we mean that their
    active flag is set to False
    """

    def get_django_type_involved(self, build_context: GraphQLBuildtimeContext) -> TDjangoModelType:
        return self.django_type(build_context)

    def _get_description_object_not_present_in_database(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        return [
            "if the object is not present, we will do nothing"
        ]

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
        try:
            result = django_type._default_manager.filter(**input_dict)
            return True, result
        except:
            return False, None

    def _delete_object_in_database(self, django_type: TDjangoModelType, items_in_db: Optional[any], runtime_context: GraphQLRuntimeContext) -> any:
        """
        This implementation will return all the items in items_in_db that have been deleted
        from the database. We set the active flag to false, then persist the change

        :inherit-doc:
        :param django_type:
        :param items_in_db:
        :param runtime_context:
        :return:
        """
        # set the object generated by the query set to inactive fields
        result = []
        for item in items_in_db:
            m: models.Model = item
            flag = type(m)._default_manager.set_active_flag_to(m, False)
            if flag:
                result.append(m)
            m.save()
        return result

    def _check_delete_object_return_value(self, result: any, django_type: TDjangoModelType, runtime_context: GraphQLRuntimeContext):
        pass

    def _delete_generate_mutation_instance_row_does_not_exists(self, mutation_class: type, item_in_db: models.Model,
                                                               runtime_context: GraphQLRuntimeContext) -> any:
        return dict(count=0, items=[])

    def _delete_generate_mutation_instance_row_deleted(self, mutation_class: type, result: List[models.Model],
                                                       runtime_context: GraphQLRuntimeContext) -> any:
        return dict(count=len(result), items=result)
