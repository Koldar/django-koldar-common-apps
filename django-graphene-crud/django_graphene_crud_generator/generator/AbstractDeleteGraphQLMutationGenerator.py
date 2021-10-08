import abc
from typing import List, Dict, Tuple, Optional

from django_koldar_utils.graphql_toolsbox.graphql_types import TDjangoModelType, TGrapheneQuery, TGrapheneArgument, \
    TGrapheneReturnType, TGrapheneWholeQueryReturnType, TGrapheneMutation

from django.db import models

from django_graphene_crud_generator.generator.AbstractGraphQLMutationGenerator import AbstractGraphQLMutationGenerator
from django_graphene_crud_generator.generator.PermissionsComponent import PermissionComponent
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext


class AbstractDeleteGraphQLMutationGenerator(AbstractGraphQLMutationGenerator):
    """
    Allows you to generate a delete endpoint.
    """

    @abc.abstractmethod
    def get_django_type_involved(self, build_context: GraphQLBuildtimeContext) -> TDjangoModelType:
        """
        The django model that we want to create with this mutation
        :param build_context: information known at compile time
        :return:
        """
        pass

    @abc.abstractmethod
    def _get_description_object_not_present_in_database(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        """
        Section of the description describing what happens if the object to remove is not present in the database

        :param build_context: information known at compile time
        :return:
        """
        pass

    def _generate_action_description(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        """
        the description of the create mutation

        :param build_context: information known at compile time
        """

        description = [
            f"Allows you to delete a previously stored instance of {self.get_django_type_involved(build_context).__name__}."
        ]
        description.extend(self._get_description_object_not_present_in_database(build_context))
        return description

    def _generate_action_class_name(self, build_context: GraphQLBuildtimeContext) -> str:
        """
        mutation class name

        :param build_context: information known at compile time
        """
        return f"Delete{self.get_django_type_involved(build_context).__name__}"

    @abc.abstractmethod
    def _check_if_object_exists(self, django_type: TDjangoModelType, runtime_context: GraphQLRuntimeContext) -> Tuple[
        bool, Optional[models.Model]]:
        """
        Check if a particular element already exists in the database

        :param django_type: type of the model to fetch
        :param runtime_context: information known at runtime (e.g., graphq info instance)
        :return: true if the object already exists in the database, false otherwise. The second item of the tuple
            represents the element already stored in the database. Notice that this value is optional for the
            implementation to implement. In other words if can be None even if the object is already present in the
            database. Useful if you want to pass additional information to the other methods after the check is complete,
            in order to avoid recomputing the same query
        """
        pass

    @abc.abstractmethod
    def _delete_object_in_database(self, django_type: TDjangoModelType, item_in_db: Optional[any], runtime_context: GraphQLRuntimeContext) -> any:
        """
        Delete an object in the database. You are ensured that the object already exists in the database

        :param django_type: type of the model to fetch
        :param item_in_db: the result generated by _check_if_object_exists. Read the implementation details to
            understand what occurs
        :param runtime_context: data availalbe to us while running the query
        :return: anything you want. It should repersents the removed row though
        """
        pass

    @abc.abstractmethod
    def _check_delete_object_return_value(self, result: any, django_type: TDjangoModelType, runtime_context: GraphQLRuntimeContext):
        """
        Check if the output of _delete_new_object_in_database represents a successful operation or not

        :param result: output of _add_new_object_in_database
        :param django_type: type of the model to fetch
        :param runtime_context: data availalbe to us while running the query
        """
        pass

    @abc.abstractmethod
    def _delete_generate_mutation_instance_row_does_not_exists(self, mutation_class: type, item_in_db: models.Model,
                                                              runtime_context: GraphQLRuntimeContext) -> any:
        """
        code used to create the instance of the create mutation class when the element to add is already
        present in the database

        :param mutation_class: type of the create mutation
        :param item_in_db: the object that is already present in the database. By contract it can be None even if
            the object is stored in the database. Do not assume anything if this value
            is None!
        :return: instance of mutation_class
        """
        pass

    @abc.abstractmethod
    def _delete_generate_mutation_instance_row_deleted(self, mutation_class: type, result: any,
                                                     runtime_context: GraphQLRuntimeContext) -> any:
        """
        code used to create the instance of the create mutation class when the element to add has
        been successfully added

        :param mutation_class: type of the create mutation
        :return: instance of mutation_class
        """
        pass

    def graphql_body_function(self, runtime_context: GraphQLRuntimeContext, *args,
                              **kwargs) -> Tuple[TGrapheneWholeQueryReturnType, bool]:
        django_type = self.get_django_type_involved(runtime_context.build_context)
        mutation_class = runtime_context.build_context.action_class

        exists, item_in_db = self._check_if_object_exists(django_type, runtime_context)
        if not exists:
            result = self._delete_generate_mutation_instance_row_does_not_exists(mutation_class, item_in_db, runtime_context)
        else:
            # delete the instance
            delete_result = self._delete_object_in_database(django_type, item_in_db, runtime_context)
            self._check_delete_object_return_value(delete_result, django_type, runtime_context)
            result = self._delete_generate_mutation_instance_row_deleted(mutation_class, delete_result, runtime_context)
        return result