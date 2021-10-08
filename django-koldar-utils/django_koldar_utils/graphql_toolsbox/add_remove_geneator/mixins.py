from typing import Optional, List

import graphene

from django.db import models

from django_koldar_utils.django_toolbox import auth_decorators
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.IAddRemoveElementGraphql import AbstractContext, ModelDefinition, AddMutationContext, \
    RemoveMutationContext


class StandardObjectFetching:
    """
    A mixin that allows to fetch and add single entities in the database.
    This mixin does not invovle relationships, only relationship objects.
    Support for IAddRemoveElementGraphQL. Almost essential in every IAddRemoveElementGraphQL implementation.

    Does not support n-ary relations
    """

    def __init__(self):
        pass

    def _is_object_in_db(self, mutation_class: type, context: AbstractContext, model_definition: ModelDefinition,
                         data: any, info: any,
                         *args, **kwargs) -> bool:
        if context.is_nary():
            raise NotImplementedError()

        # filter away inactive fields and fields set to None
        data = {k: v for k, v in data.items() if v is not None}
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
        return model_definition.django_type._default_manager.get(**data)


class PassMutationClassNameFromKwArgs:
    """
    Allows to pass the mutations names from the generate method.
    Support for IAddRemoveElementGraphQL.
    """

    def __init__(self):
        pass

    def _add_mutation_name(self, context: AddMutationContext):
        if "add_mutation_name" in context.implementation_kwargs:
            return context.implementation_kwargs["add_mutation_name"]
        else:
            return super()._add_mutation_name(context)

    def _remove_mutation_name(self, context: AddMutationContext):
        if "remove_mutation_name" in context.implementation_kwargs:
            return context.implementation_kwargs["remove_mutation_name"]
        else:
            return super()._remove_mutation_name(context)


class AllowsAuthentication:
    """
    Decorate the add mutation and the remove mutation with a ensure_user_has_permissions.
    Support for IAddRemoveElementGraphQL.

    You can customize the permissions via the kwargs:
    - add_permissions_required
    - remove_permissions_required
    """

    def __init__(self):
        pass

    def _add_mutation_actual_body(self, mutation_class, info, *args, **kwargs) -> any:
        context: AddMutationContext = kwargs[self._get_context_key()]
        if "add_permissions_required" in context.implementation_kwargs:
            dec = auth_decorators.graphql_ensure_user_has_permissions(
                perm=context.implementation_kwargs["add_permissions_required"],
            )
        else:
            dec = lambda x: x,
        return dec(super()._add_mutation_actual_body)(mutation_class, info, *args, **kwargs)

    def _remove_mutation_actual_body(self, mutation_class, info, *args, **kwargs) -> any:
        context: RemoveMutationContext = kwargs[self._get_context_key()]
        if "add_permissions_required" in context.implementation_kwargs:
            dec = auth_decorators.graphql_ensure_user_has_permissions(
                perm=context.implementation_kwargs["remove_permissions_required"],
            )
        else:
            dec = lambda x: x
        return dec(super()._remove_mutation_actual_body)(mutation_class, info, *args, **kwargs)


# RETURN VALUES


class AddMutationReturnTrue:
    """
    Support for IAddRemoveElementGraphql that makes so the add mutation just return true if successful
    """

    def _add_mutation_output_graphene_field(self, context: AddMutationContext) -> graphene.Field:
        return GraphQLHelper.return_ok(description=f"Always true if the operation is successful")

    def _alter_add_mutation_output(self, output_to_alter: any, context: AddMutationContext,
                                   model_definitions: List[ModelDefinition], relationship_end_points: List[any],
                                   info: any, *args, **kwargs):
        return True


class RemoveMutationReturnTrue:
    """
    Support for IAddRemoveElementGraphql that makes so the remove mutation just return true if successful
    """

    def _remove_mutation_output_graphene_field(self, context: RemoveMutationContext) -> graphene.Field:
        return GraphQLHelper.return_ok(description=f"Always true if the operation is successful")

    def _alter_remove_mutation_output(self, output_to_alter: any, context: AddMutationContext,
                                   model_definitions: List[ModelDefinition], relationship_end_points: List[any],
                                   info: any, *args, **kwargs):
        return True


class AddMutationReturnNumberOfElementsRemoved:
    """
    Support for IAddRemoveElementGraphql that makes so the remove mutation just return the number of relationships removed
    if successful.
    We assume that _add_association_between_models_from_db returns as data either one of the following:
     - the number of elements added;
     - a list of elements added;
     - a model instance;
     - None;

    """

    def _add_mutation_output_graphene_field(self, context: AddMutationContext) -> graphene.Field:
        """
        :return: a list of elements that will be returned from the outptu of the mutation.
            It can be whatever you want
        """
        return GraphQLHelper.returns_nonnull_int(
            description=f"number of relationships we have added"
        )

    def _alter_add_mutation_output(self, output_to_alter: any, context: AddMutationContext,
                                      model_definitions: List[ModelDefinition], info: any, *args, **kwargs):
        if output_to_alter is None:
            return 0
        if isinstance(output_to_alter, int):
            # the removal of a relationship in a through table yields a number
            return output_to_alter
        elif isinstance(output_to_alter, list):
            return len(output_to_alter)
        elif isinstance(output_to_alter, models.Model):
            return 1
        else:
            raise TypeError(f"invalid type {type(output_to_alter)}!")


class RemoveMutationReturnNumberOfElementsRemoved:
    """
    Support for IAddRemoveElementGraphql that makes so the remove mutation just return the number of relationships removed
    if successful.
    We assume that _remove_association_between_models_from_db returns as data either one of the following:
     - the number of elements added;
     - a list of elements added;
     - a model instance;
     - None;

    """

    def _remove_mutation_output_graphene_field(self, context: RemoveMutationContext) -> graphene.Field:
        """
        :return: a list of elements that will be returned from the outptu of the mutation.
            It can be whatever you want
        """
        return GraphQLHelper.returns_nonnull_int(
            description=f"number of relationships we have added"
        )

    def _alter_remove_mutation_output(self, output_to_alter: any, context: RemoveMutationContext,
                                      model_definitions: List[ModelDefinition], info: any, *args, **kwargs):
        if output_to_alter is None:
            return 0
        if isinstance(output_to_alter, int):
            # the removal of a relationship in a through table yields a number
            return output_to_alter
        elif isinstance(output_to_alter, list):
            return len(output_to_alter)
        elif isinstance(output_to_alter, models.Model):
            return 1
        else:
            raise TypeError(f"invalid type {type(output_to_alter)}!")
