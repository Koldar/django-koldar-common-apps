import abc
import functools
from typing import Dict, Optional, List, Tuple, Union, Iterable

import stringcase

import graphene

from django.db import models

from django_koldar_utils.django_toolbox import django_helpers, auth_decorators
from django_koldar_utils.graphql_toolsbox import error_codes
from django_koldar_utils.graphql_toolsbox.GraphQLAppError import GraphQLAppError
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper


class ModelDeclarationContext(object):

    def __init__(self, django_type: type, graphene_type: type, graphene_input_type: type):
        self.django_type = django_type
        self.graphene_type = graphene_type
        self.graphene_input_type = graphene_input_type


class ModelDefinition(ModelDeclarationContext):

    def __init__(self, django_type: type, graphene_type: type, graphene_input_type: type, input_name: str, data_value: any):
        super().__init__(django_type, graphene_type, graphene_input_type)
        self.input_name = input_name
        self.data_value = data_value


class AbstractContext(object):

    def __init__(self, model_types: List[ModelDeclarationContext], relation_name: str, allow_duplicated_in_trough_relationship: bool, implementation_kwargs: Dict[str, any]):
        self.model_types: List[ModelDeclarationContext] = model_types
        self.relation_name = relation_name
        self.allow_duplicated_in_trough_relationship = allow_duplicated_in_trough_relationship
        self.implementation_kwargs = implementation_kwargs
        """
        If true, the relationship may have duplicates (e.g., book 1 has author 2 and book 1 has author 2) 
        """

    def is_binary(self) -> bool:
        return len(self.model_types) == 2

    def is_nary(self) -> bool:
        return len(self.model_types) > 2

    def cardinality(self) -> int:
        return len(self.model_types)


class AddMutationContext(AbstractContext):

    def __init__(self, model_types: List[ModelDeclarationContext], relation_name: str, add_if_not_present: bool, allow_duplicated_in_trough_relationship: bool, implementation_kwargs: Dict[str, any]):
        super().__init__(model_types, relation_name, allow_duplicated_in_trough_relationship, implementation_kwargs)
        self.add_if_not_present = add_if_not_present

        self.description: str = None
        self.active_flag_name: str = None
        self.input_names: List[str] = None
        self.output_name: str = None
        self.old_length_output_name: str = None
        self.new_length_output_name: str = None
        self.added_output_name: str = None
        self.created_output_name: str = None
        self.mutation_class_name: str = None


class RemoveMutationContext(AbstractContext):

    def __init__(self, model_types: List[ModelDeclarationContext], relation_name: str,
                 ignore_if_not_present: bool, allow_duplicated_in_trough_relationship: bool, implementation_kwargs: Dict[str, any]):
        super().__init__(model_types, relation_name, allow_duplicated_in_trough_relationship, implementation_kwargs)
        self.relation_name = relation_name
        self.ignore_if_not_present = ignore_if_not_present

        self.description: str = None
        self.input_names: List[Tuple[int, str]] = None
        self.output_name: str = None
        self.elements_removed_name: str = None
        self.mutation_class_name: str = None


class IAddRemoveElementGraphql(abc.ABC):
    """
    A class that generates classes representing graphql_toolsbox queries adding adn removing items from a relationship.
    Relationship can
    """

    # ENTITY ABSTARCT METHODS

    @abc.abstractmethod
    def _get_add_mutation_relationship_specific_data(self, mutation_class: type, context: AbstractContext, model_definitions: List[ModelDefinition], relationship_end_points: List[any], info: any, *args, **kwargs) -> any:
        """
        After we have generated the endpoints of the relationship that we need to create,
        we call this method to fetch the data that is typical of thre relationship that we need to create.
        This function return value will directly be injected in _add_association_between_models_in_db

        :param mutation_class: mutation class that we are building
        :param context: global context used to fetch information
        :param model_definitions: types relative to the relationship endpoints we are checking
        :param relationship_end_points: endpoints involved in this relationship
        :param info: graphql_toolsbox info
        :param args: graphql_toolsbox args
        :param kwargs: graphql_toolsbox kwargs
        :return: the data typical to the relationship
        """
        pass

    @abc.abstractmethod
    def _add_object_to_db(self, mutation_class: type, context: AbstractContext,
                          model_definition: ModelDefinition, data: any, info, *args, **kwargs) -> Optional[any]:
        """
        Add an object passed in input to the database.
        By default we will call create with data

        :param mutation_class: mutation class that we are building
        :param django_element_type: django_toolbox element, passed from generate
        :param data: set of input parameters fo the graphql_toolsbox mutation
        :param info: graphql_toolsbox info
        :param args: graphql_toolsbox args
        :param kwargs: graphql_toolsbox kwargs
        :return: true if the object is already present in the database, false otherwise.
        """
        pass

    @abc.abstractmethod
    def _is_object_in_db(self, mutation_class: type, context: AbstractContext,
                          model_definition: ModelDefinition, data: any, info, *args, **kwargs) -> bool:
        """

        :param mutation_class: class repersenting the mutation that we need to add
        :param context: variable tha you can use to gain access to the framework data
        :param model_definition: object contaiing all the relationship endpoint models and definitions
        :param data: data that you may use to identifythe object you are looking for
        :return: true if the object is inside the database, false otherwise
        """
        pass

    @abc.abstractmethod
    def _get_object_from_db(self, mutation_class: type, context: AbstractContext,
                          model_definition: ModelDefinition, data: any, info, *args, **kwargs) -> Optional[any]:
        """
        Add an object passed in input to the database.
        By default we will call create with data

        :param mutation_class: mutation class that we are building
        :param mutation_class: class repersenting the mutation that we need to add
        :param context: variable tha you can use to gain access to the framework data
        :param model_definition: object contaiing all the relationship endpoint models and definitions
        :para data: data that you may use to identifythe object you are looking for
        :param info: graphql_toolsbox info
        :param args: graphql_toolsbox args
        :param kwargs: graphql_toolsbox kwargs
        :return: the object from the database
        """
        pass

    @abc.abstractmethod
    def _get_number_of_elements_in_association(self, context: AbstractContext, relationship_endpoints: List[any]) -> int:
        """
        :param context: context of the mutation generation
        :param relationship_endpoints: endpoint involved in the relationship to count
        :return: number of elements in the given association
        """
        pass

    @abc.abstractmethod
    def _add_association_between_models_in_db(self, context: AddMutationContext, model_definitions: List[ModelDefinition], relationship_endpoints: List[any], relationship_specific_data: any) -> Tuple[any, int]:
        """
        :param context: context of the mutation generation
        :param model_definitions: the relationship endpoint data that we need to add
        :param relationship_endpoints: endpoints of the relationship to add
        :return: pair
         - an object that will be put in the output of the mutation
         - number of elements added in the association
        """
        pass

    @abc.abstractmethod
    def _remove_association_between_models_from_db(self, mutation_class: type, context: RemoveMutationContext, model_definitions: List[ModelDefinition], info: any, *args, **kwargs) -> Tuple[any, int]:
        """
        Concretely remove the association of a given relationship

        :param context: context of the mutation generation
        :param relationship_to_remove: somethign that represents the relationship that we need to remove
        :return:
            - first: You can return whatever you want. We will include this elements in the mutation
                output
            - second: number of rows you have removed
        """
        pass

    # METHOD TO ADAPT OBJECTS

    def _prepare_data_before_checking_presence_in_db(self, mutation_class: type, context: AbstractContext, model_definition: ModelDefinition, data_to_check: any, info: any, *args, **kwargs) -> any:
        """
        Function use to alter the value of data_to_check before sending it to _is_object_in_db

        :param mutation_class: mutation class that we are building
        :param context: global context used to fetch information
        :param model_definition: types relative to the model we are checking
        :param data_to_check: set of input parameters fo the graphql_toolsbox mutation
        :param info: graphql_toolsbox info
        :param args: graphql_toolsbox args
        :param kwargs: graphql_toolsbox kwargs
        :return: the data to pass to _is_object_in_db
        """
        return data_to_check

    def _prepare_arguments_before_creating(self, mutation_class: type, context: AbstractContext, model_definition: ModelDefinition, data_value: any, info: any, *args, **kwargs) -> any:
        """
        Function use to alter the value of data_to_add before sending it to _add_object_to_db

        :param mutation_class: mutation class that we are building
        :param context: global context used to fetch information
        :param model_definition: types relative to the model we are checking
        :param data_to_check: set of input parameters fo the graphql_toolsbox mutation
        :param info: graphql_toolsbox info
        :param args: graphql_toolsbox args
        :param kwargs: graphql_toolsbox kwargs
        :return: the data to pass to _add_object_to_db
        """
        # create_args = {k: v for k, v in dict(model_input_as_dict_data).items() if v is not None}
        return data_value

    # ADD AND REMOVE OVERRIDEABLE METHODS

    def _get_add_mutation_input_parameter_names(self, context: AddMutationContext) -> Iterable[Tuple[int, str]]:
        """
        :return: name of the graphql_toolsbox mutation parameter representing the object to add.
        The object return as many values as the size of the relationship. first item of pairs are django_toolbox types and
        second item pairs are the input parameter types
        """

        index_types = dict()
        for i, x in enumerate(context.model_types):
            name = x.django_type.__name__
            if name not in index_types:
                index_types[name] = 0
            else:
                index_types[name] += 1

            s = index_types[name] if index_types[name] > 0 else ""
            yield i, stringcase.camelcase(f"{name}Item{s}")

    def _get_remove_mutation_input_parameter_names(self, context: RemoveMutationContext) -> Iterable[Tuple[int, str]]:
        """

        :param context: context of the mutation generation
        :return: name of the graphql_toolsbox mutation parameter representing the object to add
        """
        index_types = dict()
        for i, x in enumerate(context.model_types):
            name = x.django_type.__name__
            if name not in index_types:
                index_types[name] = 0
            else:
                index_types[name] += 1

            s = index_types[name] if index_types[name] > 0 else ""
            yield i, stringcase.camelcase(f"{name}Item{s}")

    def _get_add_mutation_output_return_value_name(self, context: AddMutationContext) -> str:
        """
        :param context: context of the mutation generation
        :return: name of the return value of the add mutation
        """
        return f"{context.relation_name}AddOutcome"

    def _get_remove_mutation_output_return_value_name(self, context: RemoveMutationContext) -> str:
        """
        :param context: context of the mutation generation
        :return: name of the return value of the add mutation
        """
        return f"{stringcase.camelcase(context.relation_name)}RemoveOutcome"

    def _configure_add_mutation_inputs(self, original_arguments: Dict[str, graphene.Field], context: AddMutationContext) -> Dict[
        str, graphene.Field]:
        """
        The inputs the add mutation may have. Use this fuield to add additional mutation inputs

        :param original_arguments: the inputs the add mutation by default have
        :param context: context used to fetch shared information
        :return: a dictioanry repersenting the arguments of the add mutation
        """
        return original_arguments

    def _configure_remove_mutation_inputs(self, original_arguments: Dict[str, graphene.Field], context: RemoveMutationContext) -> Dict[
        str, graphene.Field]:
        """
        The inputs the add mutation may have. Use this fuield to add additional mutation inputs

        :param original_arguments: the inputs the add mutation by default have
        :param context: context used to fetch shared information
        :return: a dictioanry repersenting the arguments of the add mutation
        """
        return original_arguments

    def _add_mutation_name(self, context: AddMutationContext) -> str:
        """
        Generate the name of the class representing the add mutation

        :param context: context of the mutation generation
        :return: name of the mutation that adds elements to the relationship
        """
        return f"Add{stringcase.pascalcase(context.relation_name)}Of{''.join(map(lambda x: stringcase.pascalcase(x.django_type.__name__), context.model_types))}"

    def _remove_mutation_name(self, context: RemoveMutationContext) -> str:
        """
        Generate the name of the class representing the remove mutation

        :param context: context of the mutation generation
        :return: name of the mutation that adds elements to the relationship
        """
        return f"Remove{stringcase.pascalcase(context.relation_name)}Of{''.join(map(lambda x: stringcase.pascalcase(x.django_type.__name__), context.model_types))}"

    def _get_add_mutation_description(self, context: AddMutationContext) -> str:
        """
        :param context: context of the mutation generation
        :return: description of the addmutation
        """
        if context.add_if_not_present:
            not_present = "We will persist it first by creating the object"
        else:
            not_present = "We will raise exception"
        dsc = f"""Allows to add a new association of the relation {context.relation_name} for the type {', '.join(map(lambda x: x.django_type.__name__, context.model_types))}. If an element
            is already within such a list we do nothing. If the element input that is an endpoint for this assoication 
            is not already persisted in the database (i.e., the input has an id not null), {not_present}. 
            If the item to add has the active flag set to False, we do nothing. 
            The function returns the element added in the relationship as well as the previous and after length of the
            collection w.r.t. the add operation. We will also return whether or not we actually have added the
            new item to the collection and if we had to first create a new item in the database.
            """
        return dsc

    def _get_remove_mutation_description(self, context: RemoveMutationContext) -> str:
        """
        :param context: context of the mutation generation
        :return description of the remove mutation
        """
        if context.ignore_if_not_present:
            not_present = "we will do nothing"
        else:
            not_present = "we will raise exception"
        dsc = f"""Allows to remove a relationship between the objects 
            {', '.join(map(lambda x: x.django_type.__name__, context.model_types))} previously created. 
            The relationship involved is \"{context.relation_name}\". If we are 
            requested to remove an element which is not in the list, {not_present}. 
            If the item to remove exists and has the active flag set to False, we do nothing. 
            The function returns the element added in the relationship as well as the previous and after length
            of the collection w.r.t. the remove operation. We will also return whether or not we actually 
            have removed the item to the collection. With this mutation you can remove multiple items in one sweep.
            """
        return dsc

    @abc.abstractmethod
    def _add_mutation_output_graphene_field(self, context: AddMutationContext) -> graphene.Field:
        """
        Concretely, this is the first item of the return value of _add_association_between_models_in_db.
        Be sure that this function and _add_association_between_models_in_db has a matching result

        :param context: context to fetch information
        :return: graphene_toolbox declaration of the output
        """
        pass

    @abc.abstractmethod
    def _remove_mutation_output_graphene_field(self, context: RemoveMutationContext) -> graphene.Field:
        """
        Concretely, this is the first item of the return value of _remove_association_between_models_in_db.
        Be sure that this function and _add_association_between_models_in_db has a matching result

        :param context: context to fetch information
        :return: something that will be incorporated in the remove mutation output
        """
        pass

    def _configure_add_mutation_return_type(self, original_return_type: Dict[str, graphene.Field], context: AddMutationContext) -> Dict[
        str, graphene.Field]:
        """
        Function use to customize the return type of the add mutation, for example by adding additional fields on the
        top level.

        :param original_return_type: the data that we want to add without intervent
        :param context: context used to retriev information
        :return: new graphene_toolbox types dictionary type representing the add mutation output
        """
        return original_return_type

    def _configure_remove_mutation_return_type(self, original_return_type: Dict[str, graphene.Field], context: RemoveMutationContext) -> Dict[
        str, graphene.Field]:
        """
        Function use to customize the return type of the remove mutation, for example by adding additional fields on the
        top level.

        :param original_return_type: the data that we want to add without intervent
        :param context: context used to retriev information
        :return: new graphene_toolbox types dictionary type representing the add mutation output
        """
        return original_return_type

    def _alter_add_mutation_output(self, output_to_alter: any, context: AddMutationContext, model_definitions: List[ModelDefinition], relationship_end_points: List[any], info: any, *args, **kwargs):
        """
        Function used after terminating the addition of a new relationship to prepare the result before sending it to the mutation output
        """
        return output_to_alter

    def _alter_remove_mutation_output(self, output_to_alter: any, context: RemoveMutationContext, model_definitions: List[ModelDefinition], info: any, *args, **kwargs):
        """
        Function used after terminating the addition of a new relationship to prepare the result before sending it to the mutation output
        """
        return output_to_alter

    # SHARED OVERRIDABLE FUNCTIONS

    def _get_old_length_output_name(self, context: AbstractContext) -> str:
        return f"{context.relation_name}OldLength"

    def _new_length_output_name(self, context: AbstractContext) -> str:
        return f"{context.relation_name}NewLength"

    def _added_output_name(self, context: AddMutationContext) -> str:
        return f"{context.relation_name}Added"

    def _created_output_name(self, context: AddMutationContext) -> str:
        return f"{context.relation_name}Created"

    def _get_elements_removed_name(self, context: RemoveMutationContext) -> str:
        return f"{context.relation_name}ElementsRemoved"

    # TODO remove
    # def _convert_graphql_input_to_dict(self, graphql_input: any, fields_to_check: List[graphene_toolbox.Field]) -> Dict[str, any]:
    #     result = dict()
    #     for f in fields_to_check:
    #         if not hasattr(graphql_input, f.name):
    #             continue
    #         result[f.name] = getattr(graphql_input, f.name)
    #     return result

    def _get_context_key(self) -> str:
        return "__context_from_generator"

    def _create_additional_context_fields(self, context: AbstractContext):
        """
        A function that is invoked when creatnig the mutations.
        Useful for adding keys in the context. Called both when generating add and remove mutations
        """
        pass

    # MAIN METHOD

    def generate(self, models_types: List[Tuple[type, type]],
                 relation_name: str,
                 add_if_not_present: bool = False,
                 allow_duplicated_in_trough_relationship: bool = False,
                 generate_add_mutation: bool = True,
                 generate_remove_mutation: bool = True,
                 **kwargs
                 ) -> Tuple[type, type]:
        """
        :param models_types: list of pairs. For each of them, the first represents the graphene_toolbox graphQL type while
            the second the input gaphql type. The django_toolbox model is fetched from the grpahene one
        :param relation_name: name of the relationship represented by the list
        :param allow_duplicated_in_trough_relationship: if set, we will accept that in the database there may be multiple rows in the relationship with the same data.
            Meaningful only if the relationship has a through table
        :param add_if_not_present: if this variable is set to True, if the user add a non persisteed django_element_type instance as the input of the mutation,
            we will first persist such an object
        :param generate_remove_mutation: if set, we will create a remove mutation
        :param generate_add_mutation: if set, we will create an add mutation
        :param kwargs: implementation specific data. This class does not use it at all
        :reutrn: first type representing this add element to list mutation, while the second represents the removal from this list
        """

        if generate_add_mutation:
            context = AddMutationContext(
                model_types=[ModelDeclarationContext(gt._meta.model, gt, git) for gt, git in models_types],
                relation_name=relation_name,
                add_if_not_present=add_if_not_present,
                allow_duplicated_in_trough_relationship=allow_duplicated_in_trough_relationship,
                implementation_kwargs=kwargs,
            )
            add_mutation = self._generate_add_mutation(context)
        else:
            add_mutation = None

        if generate_remove_mutation:
            context = RemoveMutationContext(
                model_types=[ModelDeclarationContext(gt._meta.model, gt, git) for gt, git in models_types],
                relation_name=relation_name,
                ignore_if_not_present=True,
                allow_duplicated_in_trough_relationship=allow_duplicated_in_trough_relationship,
                implementation_kwargs=kwargs,
            )
            remove_mutation = self._generate_remove_mutation(context)
        else:
            remove_mutation = None

        return add_mutation, remove_mutation

    # ADD MUTATION

    def _add_mutation_actual_body(self, mutation_class, info, *args, **kwargs) -> any:
        result_create = 0
        if self._get_context_key() not in kwargs:
            raise ValueError(f"Cannot find '{self._get_context_key()}' context!")
        context: AddMutationContext = kwargs[self._get_context_key()]

        # create model definitions
        model_definitions = []
        for i, x in enumerate(context.model_types):
            model_definitions.append(ModelDefinition(
                django_type=x.django_type,
                graphene_type=x.graphene_type,
                graphene_input_type=x.graphene_input_type,
                input_name=context.input_names[i][1],
                data_value=kwargs[context.input_names[i][1]] # this is already insdtance of the graphene_input_type
            ))

        # iterate over input_values and create all the relationship endpoint if necessary
        relationship_end_points = []
        for index, model_definition in enumerate(model_definitions):
            # check if the element we need to add exists in the database
            data_value = self._prepare_data_before_checking_presence_in_db(mutation_class, context, model_definition, model_definition.data_value, info, *args, **kwargs)
            if not self._is_object_in_db(mutation_class, context, model_definition, data_value, info, *args, **kwargs):
                if context.add_if_not_present:
                    # we need to create the object
                    # create argument and omits the None values
                    create_args = self._prepare_arguments_before_creating(mutation_class, context, model_definition, data_value, info, *args, **kwargs)
                    object_to_add = self._add_object_to_db(
                        mutation_class=mutation_class,
                        context=context,
                        model_definition=model_definition,
                        data=create_args,
                        info=info, *args, **kwargs
                    )
                    if object_to_add is None:
                        raise GraphQLAppError(error_codes.CREATION_FAILED, object=model_definition.django_type.__name__,
                                              values=create_args)
                    result_create = True
                else:
                    raise GraphQLAppError(error_codes.OBJECT_NOT_FOUND, object=model_definition.django_type.__name__, values=data_value)
            else:
                object_to_add = self._get_object_from_db(
                    mutation_class=mutation_class,
                    context=context,
                    model_definition=model_definition,
                    data=data_value,
                    info=info,
                    *args, **kwargs
                )
            relationship_end_points.append(object_to_add)

        # ok, now we need to concretely add the relationship
        result, added = self._add_association_between_models_in_db(
            context=context,
            model_definitions=model_definitions,
            relationship_endpoints=relationship_end_points,
            relationship_specific_data=self._get_add_mutation_relationship_specific_data(mutation_class, context, model_definitions, relationship_end_points, info, *args, **kwargs)
        )
        result = self._alter_add_mutation_output(
            output_to_alter=result,
            context=context,
            model_definitions=model_definitions,
            relationship_end_points=relationship_end_points,
            info=info, *args, **kwargs
        )

        new_len = self._get_number_of_elements_in_association(
            context=context,
            relationship_endpoints=relationship_end_points,
        )
        old_len = new_len - added
        result_added = new_len > old_len

        # yield result
        return mutation_class(**{
            context.output_name: result,
            context.added_output_name: result_added,
            context.created_output_name: result_create,
            context.old_length_output_name: old_len,
            context.new_length_output_name: new_len
        })

    def _generate_add_mutation(self, context: AddMutationContext) -> type:

        # POPULATE CONTEXT
        context.description = self._get_add_mutation_description(context)
        # context.active_flag_name = self._models_active_flag_name(context)
        context.input_names = list(self._get_add_mutation_input_parameter_names(context))
        context.output_name = self._get_add_mutation_output_return_value_name(context)
        context.old_length_output_name = self._get_old_length_output_name(context)
        context.new_length_output_name = self._new_length_output_name(context)
        context.added_output_name = self._added_output_name(context)
        context.created_output_name = self._created_output_name(context)
        context.mutation_class_name = str(self._add_mutation_name(context))
        self._create_additional_context_fields(context)

        # POPULATE ARGUMENTS
        arguments = dict()
        for index, input_param in context.input_names:
            arguments[input_param] = GraphQLHelper.argument_required_input(
                input_type=context.model_types[index].graphene_input_type,
                description=f"one of the endpoints of the relation {context.relation_name}"
            )
        arguments = self._configure_add_mutation_inputs(arguments, context)

        # POPULATE RETURN TYPE
        return_type = {
                context.output_name: self._add_mutation_output_graphene_field(context),
                context.added_output_name: GraphQLHelper.returns_nonnull_boolean(
                    description=f"True if we had added a new item in the collection, false otherwise"),
                context.created_output_name: GraphQLHelper.returns_nonnull_boolean(
                    description=f"True if we had created the new item in the database before adding it to the relation"),
                context.old_length_output_name: GraphQLHelper.returns_nonnull_int(
                    description=f"The number of elements in the collection before the add operation was performed"),
                context.new_length_output_name: GraphQLHelper.returns_nonnull_int(
                    description=f"The number of elements in the collection after the add operation was performed"),
            }
        return_type = self._configure_add_mutation_return_type(return_type, context)

        return GraphQLHelper.create_mutation(
            mutation_class_name=context.mutation_class_name,
            description=context.description,
            arguments=arguments,
            return_type=return_type,
            body=functools.partial(self._add_mutation_actual_body, **{self._get_context_key(): context})
        )

    # REMOVE MUTATION

    def _generate_remove_mutation(self, context: RemoveMutationContext) -> type:
        context.description = self._get_remove_mutation_description(context)
        context.input_names = list(self._get_remove_mutation_input_parameter_names(context))
        context.output_name = self._get_remove_mutation_output_return_value_name(context)
        context.elements_removed_name = self._get_elements_removed_name(context)
        context.mutation_class_name = str(self._remove_mutation_name(context))
        self._create_additional_context_fields(context)

        # POPULATE ARGUMENTS
        arguments = dict()
        for index, input_param in context.input_names:
            arguments[input_param] = GraphQLHelper.argument_required_input(
                input_type=context.model_types[index].graphene_input_type,
                description=f"one of the endpoints of the relation {context.relation_name} that we need to remove"
            )
        arguments = self._configure_remove_mutation_inputs(arguments, context)

        # POPULATE RETURN TYPE
        return_type = {
            context.output_name: self._remove_mutation_output_graphene_field(context),
            context.elements_removed_name: GraphQLHelper.returns_nonnull_int(
                description=f"The number of elements that we have removed from the relationship"),
        }
        return_type = self._configure_remove_mutation_return_type(return_type, context)

        return GraphQLHelper.create_mutation(
            mutation_class_name=context.mutation_class_name,
            description=context.description,
            arguments=arguments,
            return_type=return_type,
            body=functools.partial(self._remove_mutation_actual_body, **{self._get_context_key(): context})
        )

    def _remove_mutation_actual_body(self, mutation_class, info, *args, **kwargs) -> any:
        if self._get_context_key() not in kwargs:
            raise ValueError(f"Cannot find '{self._get_context_key()}' context!")
        context: RemoveMutationContext = kwargs[self._get_context_key()]

        # input parameter may be a single value, or a list.
        # Who knows? If it is not a list, we make a list of it

        # create model definitions
        model_definitions = []
        for i, x in enumerate(context.model_types):
            model_definitions.append(ModelDefinition(
                django_type=x.django_type,
                graphene_type=x.graphene_type,
                graphene_input_type=x.graphene_input_type,
                input_name=context.input_names[i][1],
                data_value=kwargs[context.input_names[i][1]]  # this is already insdtance of the graphene_input_type
            ))

        # for every element in the list "primary_input_value", we try to remove it
        rows_removed = 0

        result, removed = self._remove_association_between_models_from_db(
            mutation_class=mutation_class,
            context=context,
            model_definitions=model_definitions,
            info=info,
            *args,
            **kwargs
        )
        rows_removed += removed
        result = self._alter_remove_mutation_output(
            output_to_alter=result,
            context=context,
            model_definitions=model_definitions,
            info=info, *args, **kwargs
        )

        if removed == 0 and not context.ignore_if_not_present:
            raise GraphQLAppError(error_codes.OBJECT_NOT_FOUND,
                                  object=context.model_types[0].django_type.__name__,
                                  values=model_definitions
            )

        # yield result
        return mutation_class(**{
            context.output_name: result,
            context.elements_removed_name: rows_removed
        })











