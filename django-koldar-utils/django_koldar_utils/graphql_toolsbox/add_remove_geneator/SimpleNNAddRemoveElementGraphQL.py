from typing import List, Tuple

import graphene

from django_koldar_utils.django_toolbox import django_helpers
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.IAddRemoveElementGraphql import IAddRemoveElementGraphql, AbstractContext, \
    ModelDefinition, AddMutationContext, RemoveMutationContext
from django_koldar_utils.graphql_toolsbox.add_remove_geneator.mixins import StandardObjectFetching, \
    PassMutationClassNameFromKwArgs


class AbstractSimpleNNAddRemoveElementGraphQL(StandardObjectFetching, IAddRemoveElementGraphql):
    """
    create adds and remove mutation that manage a particular NN relation that does not have a through table.
    The relation ship has no though table nor additional data.
    To agument this class, use a mixin in mixins module
    """

    def __check_relation(self, context: AbstractContext):
        manager = getattr(context.model_types[0].django_type, self.relationship_manager(context))
        if context.is_nary():
            raise ValueError(f"The class can manage only simple NN relations")
        if hasattr(manager, "through"):
            raise ValueError(f"The class can manage only simple NN relations")

    def relationship_manager(self, context: AbstractContext) -> str:
        """
        :returns: the name of the field in a N-N relationship endpoint **owning** the relationship
            repersenting the manager that manages the relationship. Can be a simple one or via a through table
        """
        return context.implementation_kwargs["relationship_manager"]

    def active_flag_name(self, context: AbstractContext) -> str:
        """
        :returns: name of the flag in models representing the fact that the row should actually be included in the query sets
        """
        return context.implementation_kwargs["active_flag_name"]

    def _get_add_mutation_relationship_specific_data(self, mutation_class: type, context: AbstractContext,
                                                     model_definitions: List[ModelDefinition],
                                                     relationship_end_points: List[any], info: any, *args,
                                                     **kwargs) -> any:
        return {}

    def _get_number_of_elements_in_association(self, context: AbstractContext, relationship_endpoints: List[any]) -> int:
        self.__check_relation(context)
        manager = getattr(context.model_types[0].django_type, self.relationship_manager(context))
        return manager.all().count()

    def _add_association_between_models_in_db(self, context: AddMutationContext, model_definitions: List[ModelDefinition], relationship_endpoints: List[any], relationship_specific_data: any) -> Tuple[any, int]:
        self.__check_relation(context)
        result = getattr(context.model_types[0].django_type, self.relationship_manager(context)).add(relationship_endpoints)
        return result, 1

    def _remove_association_between_models_from_db(self, mutation_class: type, context: RemoveMutationContext, model_definitions: List[ModelDefinition], info: any, *args, **kwargs) -> Tuple[any, int]:
        self.__check_relation(context)
        manager = getattr(context.model_types[0].django_type, self.relationship_manager(context))
        # assume the first object is the main one
        d = dict()
        raise NotImplementedError()
        # for model_definition in model_definitions:
        #     d[model_definition.] = django_helpers.get_first_unique_field_value(model_definition.)
        # for input_index, through_field_name in self.mapping_input_to_through_models(context).items():
        #     if input_index == 0:
        #         # skip the first model, sicne we use its manager to select the item to remove
        #         continue
        #     # for each relationship endpoint, fetch a unique field name and put it in d
        #     unique_field_name: str = list(django_helpers.get_unique_field_names(model_definitions[input_index].django_type))[0].name
        #     d[through_field_name] = getattr(model_definitions[input_index].data_value, unique_field_name)
        # result = manager.filter(**d).delete()
        # return result, 1
