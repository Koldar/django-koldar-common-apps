from typing import List, Optional, Dict, Tuple

import graphene
from django.db import models

from django_koldar_utils.django_toolbox import django_helpers
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.IAddRemoveElementGraphql import RemoveMutationContext, ModelDefinition, \
    IAddRemoveElementGraphql, AbstractContext, AddMutationContext
from django_koldar_utils.graphql_toolsbox.add_remove_geneator.mixins import PassMutationClassNameFromKwArgs, AllowsAuthentication


class SimpleAddRemoveElementGraphQL(PassMutationClassNameFromKwArgs, AllowsAuthentication, IAddRemoveElementGraphql):
    """
    A IAddRemoveElementGraphql that manage a N-N relationship.
    Rermoveal of terminary relations is not supported.

    The remove mutation works by using ids of each input. It yields the number of rows deleted
    """

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

    def mapping_input_to_through_models(self, context: AbstractContext) -> Dict[int, str]:
        """
        :returns: in order to add a through table we need to determione which relationship endpoint
            should be set to which through table model field. This dictionary tells us exactly that: for each mutation
            input parameter index (0 means the first one, 1 means the second one and so on) we need to specify the
            model field in the through table.
        """
        return context.implementation_kwargs["mapping_input_to_through_models"]

    def _is_object_in_db(self, mutation_class: type, context: AbstractContext, model_definition: ModelDefinition, data: any, info: any,
                                *args, **kwargs) -> bool:
        if context.is_nary():
            raise NotImplementedError()
        # filter away inactive fields and fields set to None
        data = {k: v for k, v in data.items() if v is not None}
        data[self.active_flag_name(context)] = True
        return model_definition.django_type._default_manager.filter(**data).count() > 0

    def _add_object_to_db(self, mutation_class: type, context: AbstractContext,
                          model_definition: ModelDefinition, data: any, info, *args, **kwargs) -> Optional[any]:
        if context.is_nary():
            raise NotImplementedError()
        # filter away fields set to None
        data = {k: v for k, v in data.items() if v is not None}
        return model_definition.django_type._default_manager.create(**data)

    def _get_object_from_db(self, mutation_class: type, context: AbstractContext,
                          model_definition: ModelDefinition, data: any, info, *args, **kwargs) -> Optional[any]:
        if context.is_nary():
            raise NotImplementedError()
        data = {k: v for k, v in data.items() if v is not None}
        data[self.active_flag_name(context)] = True
        return model_definition.django_type._default_manager.get(**data)

    def _get_add_mutation_relationship_specific_data(self, mutation_class: type, context: AbstractContext,
                                                     model_definitions: List[ModelDefinition],
                                                     relationship_end_points: List[any], info: any, *args,
                                                     **kwargs) -> any:
        return {}

    def _add_mutation_output_graphene_field(self, context: AddMutationContext) -> graphene.Field:
        return GraphQLHelper.returns_nonnull_id(description=f"unique id representing the relationship")

    def _remove_mutation_output_graphene_field(self, context: RemoveMutationContext) -> graphene.Field:
        """
        :return: a list of elements that will be returned from the outptu of the mutation.
            It can be whatever you want
        """
        return GraphQLHelper.returns_nonnull_int(
            description=f"number of relationships we have removed"
        )

    def _get_number_of_elements_in_association(self, context: AbstractContext, relationship_endpoints: List[any]) -> int:
        manager = getattr(context.model_types[0].django_type, self.relationship_manager(context))
        if context.is_nary():
            raise NotImplementedError()

        if hasattr(manager, "through"):
            # we fetch all the through value of the first model in the relationship
            through_model = manager.through
            # most likely the value of id
            unique_field_to_poll = django_helpers.get_first_unique_field_value(relationship_endpoints[0])
            result = through_model._default_manager.filter(**{self.mapping_input_to_through_models(context)[0]: unique_field_to_poll}).count()
            return result
        else:
            return manager.all().count()

    def _add_association_between_models_in_db(self, context: AddMutationContext, model_definitions: List[ModelDefinition], relationship_endpoints: List[any], relationship_specific_data: any) -> Tuple[any, int]:
        manager = getattr(context.model_types[0].django_type, self.relationship_manager(context))
        if hasattr(manager, "through"):
            through_model = manager.through
            # create a new through model
            d = dict()
            for input_index, through_field_name in self.mapping_input_to_through_models(context).items():
                d[through_field_name] = relationship_endpoints[input_index]
            # check if the value is present in the database
            already_present = through_model._default_manager.filter(**{**d, **dict(relationship_specific_data)}).count()
            if already_present == 0 or (already_present > 0 and context.allow_duplicated_in_trough_relationship):
                result = through_model._default_manager.create(**{**d, **dict(relationship_specific_data)})
                result_id = django_helpers.get_first_unique_field_value(result)
                return result, 1
            else:
                return None, 0
        else:
            result = getattr(context.model_types[0].django_type, self.relationship_manager(context)).add(relationship_endpoints)
            result_id = django_helpers.get_first_unique_field_value(result)
            return result, 1

    def _remove_association_between_models_from_db(self, mutation_class: type, context: RemoveMutationContext, model_definitions: List[ModelDefinition], info: any, *args, **kwargs) -> Tuple[any, int]:
        manager = getattr(context.model_types[0].django_type, self.relationship_manager(context))
        if context.is_nary():
            raise NotImplementedError()
        if hasattr(manager, "through"):
            # we fetch ids of each
            through_model = manager.through
            d = dict()
            for input_index, through_field_name in self.mapping_input_to_through_models(context).items():
                # for each relationship endpoint, fetch a unique field name and put it in d
                unique_field_name: str = list(django_helpers.get_unique_field_names(model_definitions[input_index].django_type))[0].name
                d[through_field_name] = getattr(model_definitions[input_index].data_value, unique_field_name)
            rows_removed, rows_deleted_per_model = through_model._base_manager.filter(**d).delete()
            return rows_removed, rows_removed
        else:
            # assume the first object is the main one
            d = dict()
            for input_index, through_field_name in self.mapping_input_to_through_models(context).items():
                if input_index == 0:
                    # skip the first model, sicne we use its manager to select the item to remove
                    continue
                # for each relationship endpoint, fetch a unique field name and put it in d
                unique_field_name: str = list(django_helpers.get_unique_field_names(model_definitions[input_index].django_type))[0].name
                d[through_field_name] = getattr(model_definitions[input_index].data_value, unique_field_name)
            result = manager.filter(**d).update(**{self.active_flag_name(context): False})
            return result, 1

    def _alter_add_mutation_output(self, output_to_alter: any, context: AddMutationContext,
                                   model_definitions: List[ModelDefinition], relationship_end_points: List[any],
                                   info: any, *args, **kwargs):
        if output_to_alter is None:
            return 0
        else:
            unique = django_helpers.get_first_unique_field_value(output_to_alter)
            return int(unique)

    def _alter_remove_mutation_output(self, output_to_alter: any, context: RemoveMutationContext,
                                      model_definitions: List[ModelDefinition], info: any, *args, **kwargs):
        if isinstance(output_to_alter, int):
            # the removal of a relationship in a through table yields a number
            return 1
        elif isinstance(output_to_alter, list):
            return len(output_to_alter)
        elif isinstance(output_to_alter, models.Model):
            model_returned: models.Model = output_to_alter
            return 1
            # return int(django_helpers.get_first_unique_field_value(model_returned))
        else:
            raise TypeError(f"invalid type {type(output_to_alter)}!")