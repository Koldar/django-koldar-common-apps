from typing import Dict

import stringcase
from django.db.models import QuerySet
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneArgument
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper

from django_graphene_crud_generator.crud_generator.contexts import CRUDBuildContext, CRUDRuntimeContext


class ReadStandardMixIn:
    """
    We implement ther ead operations.
    both read single and read all accept a single optional input parameter that is used to retrieve
    the elements satisfying the non null fields in the input
    """

    def _read_mutation_input_parameter(self, build_context: CRUDBuildContext) -> str:
        """
        Name of the parameter in create mutation that defines the element to add
        """
        return f"{stringcase.camelcase(build_context.django_type.__name__)}Match"

    def _get_read_single_queryset_filter(self, queryset: QuerySet, runtime_context: CRUDRuntimeContext) -> QuerySet:
        return self._get_read_all_queryset_filter(queryset,runtime_context)

    def _read_single_query_arguments(self, build_context: CRUDBuildContext) -> Dict[str, TGrapheneArgument]:
        return self._read_all_query_arguments(build_context)

    def _get_read_all_queryset_filter(self, queryset: QuerySet, runtime_context: CRUDRuntimeContext) -> QuerySet:
        input_name = self._read_mutation_input_parameter(runtime_context.build_context)
        match = runtime_context.get_parameter(input_name)
        if match is None:
            match = dict()
        # filter out None value
        d = dict()
        for k, v in dict(match).items():
            if v is not None:
                d[k] = v
        return queryset.filter(**d)

    def _read_all_query_arguments(self, build_context: CRUDBuildContext) -> Dict[str, TGrapheneArgument]:
        result = dict()
        input_name = self._read_mutation_input_parameter(build_context)
        result[input_name] = GraphQLHelper.argument_nullable_input(build_context.graphene_input_type)
        return result