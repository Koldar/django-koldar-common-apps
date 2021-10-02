import abc
from typing import List, Tuple, Optional

from django.db import models
from django_koldar_utils.graphql_toolsbox import error_codes
from django_koldar_utils.graphql_toolsbox.GraphQLAppError import GraphQLAppError
from django_koldar_utils.graphql_toolsbox.graphql_types import TDjangoModelType, TGrapheneWholeQueryReturnType

from django_graphene_crud_generator.generator.AbstractGraphQLQueryGenerator import \
    AbstractGraphQLQueryGenerator
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext


class AbstractReadGraphQLQueryGenerator(AbstractGraphQLQueryGenerator):
    """
    Allows you to generate a read endpoint. We do not care if the user wants to retrieve one or more elements.
    This class allows you to implement any read graphql resolver.
    """

    @abc.abstractmethod
    def get_django_type_involved(self, build_context: GraphQLBuildtimeContext) -> TDjangoModelType:
        """
        The django model that we want to create with this query
        :param build_context: information known at compile time
        :return:
        """
        pass

    @abc.abstractmethod
    def _get_description_object_not_found(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        """
        Section of the description describing what happens if we cannot find the requested object

        :param build_context: information known at compile time
        :return:
        """
        pass

    @abc.abstractmethod
    def _get_description_object_multiple_objects_found(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        """
        Section of the description describing what happens if for some weird reason multiple objects satisfying the condition
        are found

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
            f"""Allows you to fetch preexisting instances of {self.get_django_type_involved(build_context).__name__}
            that satisfies the criteria represented by the query parameters.
            """
        ]
        description.extend(self._get_description_object_not_found(build_context))
        description.extend(self._get_description_object_multiple_objects_found(build_context))
        return description

    def _generate_action_class_name(self, build_context: GraphQLBuildtimeContext) -> str:
        """
        query class name

        :param build_context: information known at compile time
        :return: the name that the class generated by this generator will have
        """
        return f"GetSingle{self.get_django_type_involved(build_context).__name__}"

    @abc.abstractmethod
    def _get_objects(self, django_type: TDjangoModelType, runtime_context: GraphQLRuntimeContext) -> Tuple[List[models.Model], Optional[any]]:
        """
        Retrieve all the object that satisfies the criteria represented by the graphql parameters

        :param django_type: type of the model to fetch
        :param runtime_context: information known at runtime (e.g., graphq info instance, graphql parameters)
        :return: an iterable containing all the elements compliant with the criteria. The second optional parameter
        represents any data that you want to pass to the enxt methods. Its semantic is implementation dependent
        and it is completely optional.
        """
        pass

    @abc.abstractmethod
    def _check_return_value(self, iterable_to_return: List[models.Model], additional_data: Optional[any], django_type: TDjangoModelType, runtime_context: GraphQLRuntimeContext):
        """
        Check if the output of _get_objects represents a successful operation or not.
        If you need to raise exceptions, here is the place to do so.

        :param iterable_to_return: first item of the output of _get_objects
        :param additional_data: second item of the output of _get_objects
        :param django_type: type of the model to fetch
        :param runtime_context: data availalbe to us while running the query
        """
        pass

    @abc.abstractmethod
    def _read_generate_query_instance_no_results(self, mutation_class: type, additional_data: Optional[any],
                                                              runtime_context: GraphQLRuntimeContext) -> any:
        """
        code used to create the instance of the read query class when the we were unable to find any element in
        the system

        :param mutation_class: type of the create mutationts
        :param additional_data: second item of the output of _get_objects
        :return: instance of mutation_class
        """
        pass

    @abc.abstractmethod
    def _read_generate_query_instance_one_result(self, mutation_class: type, result: models.Model, additional_data: Optional[any],
                                                     runtime_context: GraphQLRuntimeContext) -> any:
        """
        code used to create the instance of the create mutation class when the element to add has
        been successfully added

        :param mutation_class: type of the create mutation
        :param result: the only item present in the first coordinate of the output of _get_objects
        :param additional_data: second item of the output of _get_objects
        :return: instance of mutation_class
        """
        pass

    @abc.abstractmethod
    def _read_generate_query_instance_several_results(self, mutation_class: type, items_number: int, iterable_to_return: List[models.Model], additional_data: Optional[any], runtime_context: GraphQLRuntimeContext) -> any:
        """
        code used to create the instance of the create mutation class when the element to add has
        been successfully added

        :param mutation_class: type of the create mutation
        :param items_number: length of the list iterable_to_return
        :param iterable_to_return: first item of the output of _get_objects
        :param additional_data: second item of the output of _get_objects
        :return: instance of mutation_class
        """
        pass

    def graphql_body_function(self, runtime_context: GraphQLRuntimeContext, *args,
                              **kwargs) -> Tuple[TGrapheneWholeQueryReturnType, bool]:
        django_type = self.get_django_type_involved(runtime_context.build_context)
        mutation_class = runtime_context.build_context.action_class

        item_in_db, additional_data = self._get_objects(django_type, runtime_context)
        self._check_return_value(item_in_db, additional_data, django_type, runtime_context)
        items_in_db = list(item_in_db)
        length = len(items_in_db)
        if length == 0:
            result = self._read_generate_query_instance_no_results(mutation_class, additional_data, runtime_context)
        elif length == 1:
            result = self._read_generate_query_instance_one_result(mutation_class, item_in_db[0], additional_data, runtime_context)
        else:
            result = self._read_generate_query_instance_several_results(mutation_class, length, item_in_db, additional_data, runtime_context)
        return result


class AbstractReadAllReturnAllQuery(AbstractReadGraphQLQueryGenerator, abc.ABC):
    """
    Represents a generator that search for a set of items. If it cannot find it, it returns an empty list.
    otherwise it returns the list of them.

    When the function returns successfully, we return always a dictionary with 2 key:
     - count: number of elements returned;
     - items: lost of elements returned
    """

    def _get_description_object_not_found(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        return [
            "If the object cannot be found, we return empty list"
        ]

    def _get_description_object_multiple_objects_found(self, build_context: GraphQLBuildtimeContext) -> List[str]:
        return [
            "If the object cannot be found, we retrieve all of them"
        ]


    def _read_generate_query_instance_no_results(self, mutation_class: type, additional_data: Optional[any],
                                                 runtime_context: GraphQLRuntimeContext) -> any:
        return dict(count=0, items=[])

    def _read_generate_query_instance_one_result(self, mutation_class: type, result: models.Model,
                                                 additional_data: Optional[any],
                                                 runtime_context: GraphQLRuntimeContext) -> any:
        return dict(count=1, items=[result])

    def _read_generate_query_instance_several_results(self, mutation_class: type, items_number: int,
                                                      iterable_to_return: List[models.Model],
                                                      additional_data: Optional[any],
                                                      runtime_context: GraphQLRuntimeContext) -> any:

        return dict(count=1, items=iterable_to_return)

    def _check_return_value(self, iterable_to_return: List[models.Model], additional_data: Optional[any],
                            django_type: TDjangoModelType, runtime_context: GraphQLRuntimeContext):
        pass