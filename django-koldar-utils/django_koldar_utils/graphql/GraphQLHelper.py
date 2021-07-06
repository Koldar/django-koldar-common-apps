import abc
from typing import List, Tuple, Dict, Any, Callable, Union, Optional

import graphene
import inflect as inflect
import stringcase
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from django_koldar_utils.django import filters_helpers, django_helpers, permissions_helpers
from django_koldar_utils.graphql import graphql_decorators, error_codes
from django_koldar_utils.graphql.GraphQLAppError import GraphQLAppError

MUTATION_FIELD_DESCRIPTION = "Mutation return value. Do not explicitly use it."
"""
A prefix to put to every mutation return value"""


class ICrudOperationNamer(abc.ABC):
    """
    Class used to determine crud operation names
    """

    @abc.abstractmethod
    def get_create_name(self, django_type: type) -> Optional[str]:
        """
        fetch the name corresponding to the create mutation

        :param django_type: type of the django model (the one extending models.Model)
        :return: name of the create mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_create_return_value_name(self, django_type: type) -> Optional[str]:
        """
        Fetch the name corresponding to the return value of the create mutation

        :param django_type: type of the django model (the one extending models.Model)
        :return return value of the creqte mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_read_all_name(self, django_type: type) -> Optional[str]:
        """
        fetch the name corresponding to the read all query

        :param django_type: type of the django model (the one extending models.Model)
        :return: name of the read all query. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_read_all_return_value_name(self, django_type: type, django_filter_instance) -> Optional[str]:
        """

        :param django_type: type of the django model (the one extending models.Model)
        :param django_filter_instance: instance of a class representing a django query set filter (the one that will be
        used to implement the read all query)
        :return: name of the return value fo the read all query. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_read_single_by_primary_key_name(self, django_type: type, primary_key_name: str) -> Optional[str]:
        """
        fetch the name corresponding to the read single by primary key mutation

        :param django_type: type of the django model (the one extending models.Model)
        :param primary_key_name: name of the primary key
        :return: name of the read single by primary key mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_read_single_by_primary_key_return_value_name(self, django_type: type, primary_key: str, django_filter_instance) -> Optional[
        str]:
        """
        fetch the name corresponding to the return value of read single by primary key mutation

        :param django_type: type of the django model (the one extending models.Model)
        :param primary_key: name fo the primary key of the model
        :param django_filter_instance: instance of a class representing a django query set filter (the one that will be
        used to implement the read all query)
        :return: name of the return value of read single by primary key mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_update_name(self, django_type: type) -> Optional[str]:
        """
        fetch the name corresponding to the update mutation

        :param django_type: type of the django model (the one extending models.Model)
        :return: name of the update mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_update_return_value_name(self, django_type: type) -> Optional[str]:
        """
        fetch the return value name corresponding to the update mutation

        :param django_type: type of the django model (the one extending models.Model)
        :return: name of the return value of update mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_delete_name(self, django_type: type) -> Optional[str]:
        """
        fetch the name corresponding to the delete mutation

        :param django_type: type of the django model (the one extending models.Model)
        :return: name of the delete mutation. If None we decide
        """
        pass

    @abc.abstractmethod
    def get_delete_return_value_name(self, django_type: type) -> Optional[str]:
        """
        fetch the return value name corresponding to the delete mutation

        :param django_type: type of the django model (the one extending models.Model)
        :return: name of the return value of the delete mutation. If None we decide
        """
        pass


class StandardCrudOperationNamer(ICrudOperationNamer):
    """
    Default implementation generating standard CRUD names
    """

    def get_read_single_by_primary_key_return_value_name(self, django_type: type, primary_key_name: str, django_filter_instance) -> Optional[
        str]:
        return None

    def get_update_return_value_name(self, django_type: type) -> Optional[str]:
        return None

    def get_delete_return_value_name(self, django_type: type) -> Optional[str]:
        return None

    def get_read_all_return_value_name(self, django_type: type, django_filter_instance) -> Optional[str]:
        return None

    def get_create_name(self, django_type: type) -> Optional[str]:
        return f"Create{django_type.__name__}"

    def get_create_return_value_name(self, django_type: type) -> Optional[str]:
        return None

    def get_read_all_name(self, django_type: type) -> Optional[str]:
        return f"GetAll{django_type.__name__}"

    def get_read_single_by_primary_key_name(self, django_type: type, primary_key_name: str) -> Optional[str]:
        return f"Get{django_type.__name__}By{stringcase.pascalcase(primary_key_name)}"

    def get_update_name(self, django_type: type) -> Optional[str]:
        f"UpdatePrimitive{django_type.__name__}"

    def get_delete_name(self, django_type: type) -> Optional[str]:
        return f"MarkInactive{django_type.__name__}"


class NamespacedCrudOperationNamer(ICrudOperationNamer):
    """
    An operation namer that prefix the name of query and mutations with a string. Useful in federated schemas,
    where multiple queries with similar names namy exist.
    """

    def __init__(self, prefix: str, suffix: str = None):
        """
        :param prefix: string to put before the model name in the query/mutation names
        :param suffix: string to put after the model name in the query/mutation names
        """
        self.prefix = stringcase.pascalcase(str(prefix))
        self.suffix = stringcase.pascalcase(str(suffix))

    def get_create_name(self, django_type: type) -> Optional[str]:
        return f"Create{self.prefix}{django_type.__name__}{self.suffix}"

    def get_create_return_value_name(self, django_type: type) -> Optional[str]:
        return f"{self.prefix}{django_type.__name__}{self.suffix}Created"

    def get_read_all_name(self, django_type: type) -> Optional[str]:
        return f"GetAll{self.prefix}{django_type.__name__}{self.suffix}"

    def get_read_all_return_value_name(self, django_type: type, django_filter_instance) -> Optional[str]:
        return f"{self.prefix}{stringcase.camelcase(django_filter_instance)}{self.suffix}"

    def get_read_single_by_primary_key_name(self, django_type: type, primary_key_name: str) -> Optional[str]:
        return f"Get{self.prefix}{django_type.__name__}By{stringcase.pascalcase(primary_key_name)}{self.suffix}"

    def get_read_single_by_primary_key_return_value_name(self, django_type: type, primary_key_name: str, django_filter_instance) -> Optional[str]:
        return f"{self.prefix}{django_type.__name__}By{stringcase.pascalcase(primary_key_name)}{self.suffix}"

    def get_update_name(self, django_type: type) -> Optional[str]:
        f"UpdatePrimitive{self.prefix}{django_type.__name__}{self.suffix}"

    def get_update_return_value_name(self, django_type: type) -> Optional[str]:
        f"{self.prefix}{django_type.__name__}{self.suffix}Updated"

    def get_delete_name(self, django_type: type) -> Optional[str]:
        return f"MarkInactive{self.prefix}{django_type.__name__}{self.suffix}"

    def get_delete_return_value_name(self, django_type: type) -> Optional[str]:
        return f"{self.prefix}{django_type.__name__}{self.suffix}Deleted"


class GraphQLHelper(object):
    """
    Class used to generate relevant fields for graphql
    """

    @classmethod
    def generate_graphql_crud_of(cls,
            django_type: type, django_graphql_type: type, django_input_type: type, django_graphql_list_type: type,
            active_field_name: str = None,
            create_compare_fields: List[str] = None,
            permissions_required_create: List[str] = None,
            permissions_required_read: List[str] = None,
            permissions_required_update: List[str] = None,
            permissions_required_delete: List[str] = None,
            class_names: "ICrudOperationNamer" = None,
            generate_create: bool = True,
            generate_read_all: bool = True,
            generate_read_single: bool = True,
            generate_update: bool = True,
            generate_delete: bool = True,
                ) -> Tuple[type, type, type, type, type]:
        """
        Generate a default create, update, delete operations. Delete actually just set the active field set to false.

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene package
        :param django_input_type: class deriving from DjangoInputObjectType from django graphene extras package
        :param active_field_name: name fo the active flag
        :param create_compare_fields: field used to check uniquness of the row when creating a new element. If missing, we will populate them with all the unique fields.
            Inactive rows are ignored
        :param permissions_required_create: permissions used to create elements. If None the mutation does not required authentication
        :param permissions_required_read: permissions used to read elements. If None the mutation does not required authentication
        :param permissions_required_update: permissions used to update elements. If None the mutation does not required authentication
        :param permissions_required_delete: permissions used to delete elements. If None the mutation does not required authentication
        :param class_names: instance representing a structure that supplies the name of the queries and mutation to create.
        :param generate_create: if true, we will generate the create mutation. Otherwise we will return None as the generated mutation class
        :param generate_read_all: if true, we will generate the read all mutation. Otherwise we will return None as the generated mutation class
        :param generate_read_single: if true, we will generate the read single mutatuion. Otherwise we will return None as the generated query class
        :param generate_update: if true, we will generate the update mutatuion. Otherwise we will return None as the generated query class
        :param generate_delete: if true, we will generate the delete mutatuion. Otherwise we will return None as the generated mutation class
        :return: a tuple where each element is a class representing a mutation/query or None if the associated method "generate_" is set to False.
            - create mutation type
            - read all query type
            - update mutation type
            - delete mutation type
            - read single element query type
        """

        create = None
        read_single = None
        read_all = None
        update = None
        delete = None

        if class_names is None:
            class_names = StandardCrudOperationNamer()
        primary_key_name = django_helpers.get_name_of_primary_key(django_type)

        if generate_create:
            create = cls.generate_mutation_create(
                django_type=django_type,
                django_graphql_type=django_graphql_type,
                django_input_type=django_input_type,
                active_flag_name=active_field_name,
                fields_to_check=create_compare_fields,
                permissions_required=permissions_required_create,
                mutation_class_name=class_names.get_create_name(django_type),
                output_name=class_names.get_create_return_value_name(django_type)
            )

        if generate_read_all:
            get_all_filter = filters_helpers.create_dynamic_active_django_filter("All", django_type, active_field_name, {})
            read_all = cls.create_authenticated_list(
                django_type=django_type,
                django_graphql_type=django_graphql_type,
                get_all_filter=get_all_filter,
                permissions_required=permissions_required_read,
                query_class_name=lambda dt, ft: class_names.get_read_all_name(django_type),
                output_name=class_names.get_read_all_return_value_name(django_type, get_all_filter)
            )

        if generate_read_single:
            get_single_filter = filters_helpers.create_django_filter_returning_one_value(primary_key_name, django_type, active_field_name, {primary_key_name: ["exact"]})
            read_single = cls.generate_query_from_filter_set(
                return_single=True,
                django_type=django_type,
                django_graphql_type=django_graphql_type,
                permissions_required=permissions_required_read,
                filterset_type=get_single_filter,
                query_class_name=lambda dt, ft: class_names.get_read_single_by_primary_key_name(django_type, primary_key_name),
                output_name=class_names.get_read_single_by_primary_key_return_value_name(django_type, primary_key_name, get_single_filter)
            )

        if generate_update:
            update = cls.generate_mutation_update_primitive_data(
                django_type=django_type,
                django_graphql_type=django_graphql_type,
                django_input_type=django_input_type,
                permissions_required=permissions_required_update,
                mutation_class_name=class_names.get_update_name(django_type),
                output_name=class_names.get_update_return_value_name(django_type)
            )

        if generate_delete:
            delete = cls.generate_mutation_mark_inactive(
                django_type=django_type,
                django_graphql_type=django_graphql_type,
                django_input_type=django_input_type,
                active_flag_name=active_field_name,
                permissions_required=permissions_required_delete,
                mutation_class_name=class_names.get_delete_name(django_type),
                output_name=class_names.get_delete_return_value_name(django_type),
            )
        return create, read_all, update, delete, read_single

    # QUERY MUTATION CONSTRUCTION

    @classmethod
    def create_simple_query(cls, return_type: type, arguments: Dict[str, Any],
                            description: str = None) -> graphene.Field:
        """
        Creates a graphql query. It is simple because you need to fill out the arguments and hte other stuff by yourself.
        However with this function you can add decorators more easily.

        :: code-block:: python
            permission = create_simple_query(PermissionGraphQLType, arguments=dict(id=AbstractQuery.required_id("system permissions"), token=AbstractQuery.jwt_token()), description="fethc a given permission")

            @login_required
            @permission_required("can_permission_list")
            def resolve_permission(self, info, id: int, **kwargs):
                return Permission.objects.get(pk=id)

        :param return_type: a type extendintg DjangoGraphQLObjectType
        :param arguments: dictionary of query arguments.
        :param description: help text to show in the graphQL GUI
        :return query value. You still need to implement "def resolve_X(self, info, **kwargs):" method within the class
            containing the body of the query
        """

        return graphene.Field(return_type, description=description, **arguments)

    @classmethod
    def create_simple_authenticated_query(cls, return_type: type, arguments: Dict[str, Any],
                                          description: str = None) -> graphene.Field:
        """
        Like create_simple_query but we implicitly add a JWT token in the arguments of the query named "token"

        :: code-block:: python
            permission = create_authenticated_query(PermissionGraphQLType, arguments=dict(id=AbstractQuery.required_id("system permissions")), description="fethc a given permission")

        :param return_type: a type extendintg DjangoGraphQLObjectType
        :param arguments: dictionary of query arguments.
        :param description: help text to show in the graphQL GUI
        :return query value. You still need to implement "def resolve_X(self, info, **kwargs):" method within the class
            containing the body of the query
        """
        arguments['token'] = cls.jwt_token()
        return cls.create_simple_query(return_type=return_type, arguments=arguments, description=description)

    @classmethod
    def create_authenticated_list(cls, django_type: type, django_graphql_type: type, get_all_filter: any, permissions_required: List[str], query_class_name: Union[str, Callable[[type, type], str]] = None, output_name: Union[str, Callable[[str, any], str]] = None) -> type:
        """
        Create an authentication query allowing you to to list all the content of a particular model satisfying the specified
        filter. The return type of this query is always a list.

        :param django_type: a type representing the models.Model subclass
        :param django_graphql_type: a type representing the DjangoObjectType of the corresponding django_type
        :param get_all_filter: django query filter that implements the output of the query
        :param permissions_required: set of permissions the authenticated query needs to satisfy
        :return: type representing the graphene query list.
        """
        read_all = cls.generate_query_from_filter_set(
            return_single=False,
            django_type=django_type,
            django_graphql_type=django_graphql_type,
            permissions_required=permissions_required,
            filterset_type=get_all_filter,
            query_class_name=query_class_name,
            output_name=output_name,
        )
        return read_all

    @classmethod
    def create_authenticated_query(cls, query_class_name: str, description: str, arguments: Dict[str, type],
                        return_type: type, body: Callable, permissions_required: List[str], add_token: bool = False) -> type:
        """
        Create a graphQL query. Decorators on body will be considered

        :param query_class_name: name of the query generated
        :param description: description of the query
        :param arguments: list of arguments in input of the query. It is a dictioanry where the values are graphene
            types (e.g., graphene.String). If inputting a complex type, use graphene.Argument.
        :param return_type: return type (ObjectType) of the query.
        :param body: a callable specifiying the code of the query. The first is the query class isntance.
            Info provides graphql context. the rest are the query arguments.
            You need to return the query value
        :param permissions_required: list fo permissions required to be satisfied in order for fully using the function
        :param add_token: if set, we will add an optional token as parameter for the query
        """


        description = description + f"""The query requires authentication. Specifically, it requires the following permissions:
        {', '.join(permissions_required)}.
        """
        if add_token:
            arguments["token"] = cls.argument_jwt_token()
        return cls.create_query(
            query_class_name=query_class_name,
            description=description,
            arguments=arguments,
            output_name=stringcase.camelcase(query_class_name),
            return_type=return_type,
            body=login_required(permissions_helpers.ensure_user_has_permissions(permissions_required)(body))
        )

    @classmethod
    def create_query(cls, query_class_name: str, description: str, arguments: Dict[str, type],
                        output_name: str, return_type: type, body: Callable) -> type:
        """
        Create a graphQL query. Decorators on body will be considered

        :param query_class_name: name of the query generated
        :param description: description of the query
        :param arguments: list of arguments in input of the query. It is a dictioanry where the values are graphene
            types (e.g., graphene.String). If inputting a complex type, use graphene.Argument.
        :param output_name: name of the output variable in the graphQL language
        :param return_type: return type (ObjectType) of the query
        :param body: a callable specifiying the code of the query. The first is the query class isntance. Info provides graphql context. the rest are the query arguments. You need to return the query value
        """

        # @graphql_subquery
        # class Query(graphene.ObjectType):
        #     question = graphene.Field(
        #         QuestionType,
        #         foo=graphene.String(),
        #         bar=graphene.Int()
        #     )
        #
        #     def resolve_question(root, info, foo, bar):
        #         # If `foo` or `bar` are declared in the GraphQL query they will be here, else None.
        #         return Question.objects.filter(foo=foo, bar=bar).first()

        def perform_query(root, info, *args, **kwargs) -> any:
            if root is None:
                root = query_class
            result = body(root, info, *args, **kwargs)
            return result

        query_class = type(
            query_class_name,
            (graphene.ObjectType, ),
            {
                "__doc__": description,
                output_name: graphene.Field(return_type, args=arguments, description=description),
                f"resolve_{output_name}": perform_query
            }
        )
        # Apply decorator to auto detect queries
        query_class = graphql_decorators.graphql_subquery(query_class)

        return query_class

    @classmethod
    def generate_query_from_filter_set(cls, django_type: type, django_graphql_type: type, filterset_type: type, return_single: bool, query_class_name: Union[str, Callable[[str, str], str]] = None, permissions_required: List[str] = None, output_name: str = None) -> type:
        """
        generate a single graphQL query reprensented by the given filter_set

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene package
        :param return_single: if True, you know that the query will return a single result. Otherwise it will return a list
        :param filterset_type: filterset that will be used to generate the query
        :param permissions_required: list fo permissions that the autneticatd user needs to satisfy if she wants to gain
            access to the query. If left None, the query won't be authenticated at all
        :param output_name: name of the return value fo the qiery. It is also the name of the query altogether
        """

        p = inflect.engine()

        filterset_name = filterset_type.__name__
        if filterset_name.endswith("Filter"):
            filterset_name = filterset_name[:-len("Filter")]
        django_type_str = stringcase.pascalcase(django_type.__name__)
        filterset_type_str = stringcase.camelcase(filterset_name)
        if query_class_name is None:
            query_class_name = stringcase.pascalcase(filterset_type_str)
        else:
            if hasattr(query_class_name, "__call__"):
                # function
                query_class_name = query_class_name(django_type_str, filterset_type_str)
            elif isinstance(query_class_name, str):
                pass
            else:
                raise TypeError(f"Invalid type {type(query_class_name)}!")

        if output_name is None:
            output_name = stringcase.camelcase(filterset_type_str)

        description_multiplier = "a single" if return_single else "all the"
        description = f"""This query allow the user to retrieve {description_multiplier} active {django_type.__name__} within the system
        satisfying the following given condition: {filterset_type.__doc__}.
        """
        if permissions_required is not None:
            description += f"""The query needs authentication in order to be run. The permissions required 
            by the backend in order to properly work are: {', '.join(permissions_required)}"""

        # return type
        if return_single:
            query_return_type = django_graphql_type
        else:
            query_return_type = graphene.List(django_graphql_type)

        # the query arguments are all the single filters available in the filterset
        arguments = {}
        for filter_name in filters_helpers.get_filters_from_filterset(filterset_type):
            django_graphql_type_field = django_graphql_type._meta.fields[filter_name]
            if isinstance(django_graphql_type_field, graphene.types.field.Field):
                django_graphql_type_field_type = django_graphql_type_field.type
            else:
                django_graphql_type_field_type = django_graphql_type_field
            arguments[filter_name] = graphene.Argument(
                django_graphql_type_field_type,
                description=django_graphql_type_field.description
            )

        def body(query_class, info, *args, **kwargs) -> any:
            # query actual parameters. May be somethign of sort: {'username': 'alex', 'status': '1'}
            query_actual_parameters = {k: kwargs[k] for k in arguments if k in kwargs and k not in ("token", )}
            # see https://github.com/carltongibson/django-filter/blob/main/tests/test_filtering.py
            qs = django_type.objects.all()
            f = filterset_type(query_actual_parameters, queryset=qs)
            if return_single:
                return f.qs
            else:
                return list(f.qs)


        if permissions_required is not None:
            # add token and authentication decorators
            arguments["token"] = cls.argument_jwt_token()
            body = login_required(body)
            body = permissions_helpers.ensure_user_has_permissions(permissions_required)(body)

        result = cls.create_query(
            query_class_name=query_class_name,
            description=description,
            arguments=arguments,
            output_name=output_name,
            return_type=query_return_type,
            body=body
        )

    @classmethod
    def create_mutation(cls, mutation_class_name: str, description: str, arguments: Dict[str, any], return_type: Dict[str, any], body: Callable) -> type:
        """
        Create a generic mutation

        :param mutation_class_name: name of the subclass of graphene.Mutation that represents ths mutation
        :param description: description of the mutation. This will be shown in graphiQL
        :param arguments: argument fo the mutation. The values are set as Helper.argument_x
        :param return_type: values that the mutation will return
        :param body: function containign the mutation. return value is any.
            - 1 parameter is the mutation class name;
            - 2 parameter is info;
            - Then you can have the same parameters as the arguments (as input);
            - other parmaeters should be put in **args, **kwargs;
        """

        mutation_class_meta = type(
            "Arguments",
            (object, ),
            arguments
        )

        def mutate(root, info, *args, **kwargs) -> any:
            if root is None:
                root = mutation_class
            return body(root, info, *args, **kwargs)

        mutation_class = type(
            mutation_class_name,
            (graphene.Mutation, ),
            {
                "Arguments": mutation_class_meta,
                "__doc__": description,
                **return_type,
                "mutate": mutate
            }
        )
        # Apply decorator to auto detect mutations
        mutation_class = graphql_decorators.graphql_submutation(mutation_class)

        return mutation_class

    # todo try to code if there si tyime
    # @classmethod
    # def create_mutation_from_method(cls, f: Callable) -> type:
    #     cls.create_mutation(
    #         mutation_class_name=stringcase.pascalcase(f.__name__),
    #         description=f.__doc__,
    #         arguments=
    #     )

    @classmethod
    def create_authenticated_mutation(cls, mutation_class_name: str, description: str, arguments: Dict[str, any], return_type: Dict[str, any], body: Callable, required_permissions: List[str]) -> type:
        """
                Create a generic mutation which requires authentication. Authentication is automatically added

                :param mutation_class_name: name of the subclass of graphene.Mutation that represents ths mutation
                :param description: description of the mutation. This will be shown in graphiQL
                :param arguments: argument fo the mutation. The values are set as Helper.argument_x
                :param return_type: values that the mutation will return
                :param body: function containign the mutation. return value is any.
                    - 1 parameter is the mutation class name;
                    - 2 parameter is info;
                    - Then you can have the same parameters as the arguments (as input);
                    - other parmaeters should be put in **args, **kwargs;
                :param required_permissions: list of permissions that tjhe authenticated user needs to have before
                gain access to this function
                :return: class representing the mutation
                """

        mutation_class_meta = type(
            "Arguments",
            (object,),
            {"token": cls.argument_jwt_token(), **arguments}
        )

        description += f"""The mutation, in order to be be accessed, required user authentication. The permissions
        needed are the following: {', '.join(required_permissions)}"""

        def mutate(root, info, *args, **kwargs) -> any:
            if root is None:
                root = mutation_class
            return body(root, info, *args, **kwargs)

        mutation_class = type(
            mutation_class_name,
            (graphene.Mutation,),
            {
                "Arguments": mutation_class_meta,
                "__doc__": description,
                **return_type,
                "mutate": login_required(permissions_helpers.ensure_user_has_permissions(required_permissions)(mutate))
            }
        )
        # Apply decorator to auto detect mutations
        mutation_class = graphql_decorators.graphql_submutation(mutation_class)

        return mutation_class

    @classmethod
    def generate_mutation_create(cls, django_type: type, django_graphql_type: type, django_input_type: type, active_flag_name: str = None, fields_to_check: List[str] = None, description: str = None, input_name: str = None, output_name: str = None, permissions_required: List[str] = None, mutation_class_name: Union[str, Callable[[str], str]] = None) -> type:
        """
        Create a mutation that adds a new element in the database.
        We will generate a mutation that accepts a single input parameter. It checks if the input is not already present in the database and if not, it adds it.
        The returns the data added in the database.
        This method can already integrate graphene_jwt to authenticate and authorize users

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene package
        :param django_input_type: class deriving from DjangoInputObjectType from django graphene extras package
        :param active_flag_name: name fo the active flag
        :param fields_to_check: field used to check uniquness of the row. If missing, we will populate them with all the unique fields
        :param description: description of the create mutation
        :param input_name: the name of the only mutation argument. If unspecified, it is the camel case of the django_type
        :param output_name: the name of the only mutation return value. If unspecified, it is the camel case of the django_type
        :param permissions_required: if absent, the mutation does not require authentication. If it is non null,
            the mutation needs authentication as well as all the permissions in input.
            When authenticating a mutation, an additional "token" argument is always added
        :param mutation_class_name: a function that generates the name of the mutation type. Input argument is django_type.__name__. The output is
            the mutation name to generate. The name is then converted into pascal case automatically. If left unspecified, it is "Create{django_type.__name__}".
            Can also be a string. Note that at the end, this pascal case name will be automatically converted by graphene into camel case.
        """

        if mutation_class_name is None:
            mutation_class_name = f"Create{django_type.__name__}"
        if active_flag_name is None:
            active_flag_name = "active"
        if fields_to_check is None:
            # fetch all the unique fields
            fields_to_check = list(django_helpers.get_unique_field_names(django_type))
        if description is None:
            description = f"""Allows you to create a new instance of {django_type.__name__}. 
                If the object is already present we throw an exception.
                We raise an exception if we are able to find a row in the database with the same fields: {', '.join(fields_to_check)}.
            """
            if permissions_required is not None:
                description += f"""Note that you need to authenticate your user in order to use this mutation.
                The permission your user is required to have are: {', '.join(permissions_required)}. 
                """
        if input_name is None:
            input_name = stringcase.camelcase(django_type.__name__)
        if output_name is None:
            output_name = stringcase.camelcase(django_type.__name__)
        if hasattr(mutation_class_name, "__call__"):
            # if create_mutation_name is a function, call it
            mutation_class_name = mutation_class_name(django_type.__name__)

        def body(mutation_class, info, *args, **kwargs) -> any:
            input = kwargs[input_name]
            d = dict()
            for f in fields_to_check:
                d[f] = getattr(input, f)
            #
            d[active_flag_name] = True
            if django_type.objects.has_at_least_one(**d):
                raise GraphQLAppError(error_codes.OBJECT_ALREADY_PRESENT, object=django_type.__name__, values=d)
            # create argumejnt and omits the None values
            create_args = {k: v for k, v in dict(input).items() if v is not None}

            result = django_type.objects.create(**create_args)
            if result is None:
                raise GraphQLAppError(error_codes.CREATION_FAILED, object=django_type.__name__, values=create_args)
            return mutation_class(result)

        arguments = dict()
        arguments[input_name] = cls.argument_required_input(django_input_type, description="The object to add into the database. id should not be populated. ")
        if permissions_required is not None:
            arguments["token"] = cls.argument_jwt_token()
            body = login_required(body)
            body = permissions_helpers.ensure_user_has_permissions(permissions_required)(body)

        return cls.create_mutation(
            mutation_class_name=str(mutation_class_name),
            description=description,
            arguments=arguments,
            return_type={
                output_name: cls.returns_nonnull(django_graphql_type, description=f"the {django_type.__name__} just added into the database")
            },
            body=body
        )

    @classmethod
    def generate_mutation_update_primitive_data(cls, django_type: type, django_graphql_type: type, django_input_type: type,
                                 description: str = None, input_name: str = None,
                                 output_name: str = None, permissions_required: List[str] = None, mutation_class_name: Union[str, Callable[[str], str]] = None) -> type:
        """
        Create a mutation that revise a previously added element in the database to a newer version.
        This mutation updates only the primitive fields within the entity, jnot the relationships.
        We will generate a mutation that accepts 2 input parameters. The first is the id of the entry to alter while the second is the data to set.
        It checks if the input is not already present in the database. If not it generates an exception.
        Thefunction  returns the data that is persisted in the database after the call.
        This method can already integrate graphene_jwt to authenticate and authorize users

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene package
        :param django_input_type: class deriving from DjangoInputObjectType from django graphene extras package
        :param django_input_list_type: class derivigin from DjangoInputObjectType which repersents a list of inputs
        :param description: description of the create mutation
        :param input_name: the name of the only mutation argument. If unspecified, it is the camel case of the django_type
        :param output_name: the name of the only mutation return value. If unspecified, it is the camel case of the django_type
        :param permissions_required: if absent, the mutation does not require authentication. If it is non null,
            the mutation needs authentication as well as all the permissions in input.
            When authenticating a mutation, an additional "token" argument is always added
        :param mutation_class_name: a function that generates the name of the mutation type. Input argument is django_type.__name__. The output is
            the mutation name to generate. The name is then converted into pascal case automatically. If left unspecified, it is "Create{django_type.__name__}".
            Can also be a string. Note that at the end, this pascal case name will be automatically converted by graphene into camel case.
        """

        primary_key_name = django_helpers.get_name_of_primary_key(django_type)
        if mutation_class_name is None:
            mutation_class_name = f"UpdatePrimitive{django_type.__name__}",
        if description is None:
            description = f"""Allows you to create a new instance of {django_type.__name__}. 
                    If the object is already present we throw an exception.
                    We raise an exception if we are able to find a row in the database with the same primary key: {primary_key_name}.
                    With this mutation, it is possible to alter only the primitive fields belonging to the entity.
                    In other words, association between models cannot be altered with this mutation.
                """
            if permissions_required is not None:
                description += f"""Note that you need to authenticate your user in order to use this mutation.
                    The permission your user is required to have are: {', '.join(permissions_required)}. 
                    """
        if input_name is None:
            input_name = stringcase.camelcase(django_type.__name__)
        if output_name is None:
            output_name = stringcase.camelcase(django_type.__name__)
        if hasattr(mutation_class_name, "__call__"):
            mutation_class_name = mutation_class_name(django_type.__name__)

        def body(mutation_class, info, *args, **kwargs) -> any:
            primary_key_value: str = kwargs[primary_key_name]
            input: Any = kwargs[input_name]

            d = dict()
            d[primary_key_name] = primary_key_value
            if not django_type.objects.has_at_least_one(**d):
                raise GraphQLAppError(error_codes.OBJECT_NOT_FOUND, object=django_type.__name__, values=d)
            # create argument and omits the None values
            create_args = {k: v for k, v in dict(input).items() if v is not None}

            result = django_type.objects.find_only_or_fail(**d)
            input_as_dict = dict(input)
            for f in django_helpers.get_primitive_fields(django_type):
                name = f.attname
                if not f.is_relation and name in input_as_dict:
                    # we ignore fields that are relations
                    setattr(result, name, input_as_dict[name])
            result.save()

            return mutation_class(result)

        arguments = dict()
        arguments[primary_key_name] = cls.argument_required_id(django_type.__name__)
        arguments[input_name] = cls.argument_required_input(django_input_type,
                                                               description="The object that will update the one present in the database.")
        if permissions_required is not None:
            arguments["token"] = cls.argument_jwt_token()
            body = login_required(body)
            body = permissions_helpers.ensure_user_has_permissions(permissions_required)(body)

        return cls.create_mutation(
            mutation_class_name=str(mutation_class_name),
            description=description,
            arguments=arguments,
            return_type={
                output_name: cls.returns_nonnull(django_graphql_type,
                                                    description=f"same {django_type.__name__} you have fetched in input")
            },
            body=body
        )

    @classmethod
    def generate_mutation_delete_from_db(cls, django_type: type, django_graphql_type: type,
                                         django_input_type: type,
                                         description: str = None, input_name: str = None,
                                         output_name: str = None,
                                         permissions_required: List[str] = None,
                                         mutation_class_name: Union[str, Callable[[str], str]] = None) -> type:
        """
        Create a mutation that deletes a row stored in the database. Depending on the on_delete, this may lead to the removal of other dependant rows
        We will generate a mutation that accepts a single array of integers, each representing the ids to delete.
        If an id is not present in the database, the mutation ignores it.
        The mutation returns the set of ids that were actually removed from the database.

        This method can already integrate graphene_jwt to authenticate and authorize users

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene package
        :param django_input_type: class deriving from DjangoInputObjectType from django graphene extras package
        :param description: description of the create mutation
        :param input_name: the name of the only mutation argument. If unspecified, it is the plural form of
            the camel case of the django_type
        :param output_name: the name of the only mutation return value. If unspecified, it is "removed"
        :param permissions_required: if absent, the mutation does not require authentication. If it is non null,
            the mutation needs authentication as well as all the permissions in input.
            When authenticating a mutation, an additional "token" argument is always added
        :param mutation_class_name: a function that generates the name of the mutation type. Input argument is django_type.__name__. The output is
            the mutation name to generate. The name is then converted into pascal case automatically. If left unspecified, it is "Create{django_type.__name__}".
            Can also be a string. Note that at the end, this pascal case name will be automatically converted by graphene into camel case.
        """

        primary_key_name = django_helpers.get_name_of_primary_key(django_type)
        if mutation_class_name is None:
            mutation_class_name = f"Delete{django_type.__name__}"
        if hasattr(mutation_class_name, "__call__"):
            mutation_class_name = mutation_class_name(django_type.__name__)
        if description is None:
            description = f"""Allows you to remove a set of preexisting instances of {django_type.__name__}. 
                            If an object is not present in the database, we will skip the object deletion.
                            Object comparison is done by looking at the involved ids, each named {primary_key_name}.
                            Notice that, dependending on the database setup, we may endup removing rows from other 
                            columns as well (cascading). I
                            The mutation yields a list of ids, representing the ones that have been removed from the
                            database.
                        """
            if permissions_required is not None:
                description += f"""Note that you need to authenticate your user in order to use this mutation.
                            The permission your user is required to have are: {', '.join(permissions_required)}. 
                            """
        if input_name is None:
            p = inflect.engine()
            input_name = p.plural(stringcase.camelcase(django_type.__name__))
        if output_name is None:
            output_name = "removed"

        def body(mutation_class, info, *args, **kwargs) -> any:
            id_list: List[int] = kwargs[input_name]

            result = []
            for i in id_list:
                obj = django_type.objects.find_only_or_None(pk=i)
                if obj is not None:
                    result.append(getattr(obj, primary_key_name))
                    obj.delete()

            return mutation_class(result)

        arguments = dict()
        arguments[input_name] = cls.argument_required_id_list(django_type.__name__)
        if permissions_required is not None:
            arguments["token"] = cls.argument_jwt_token()
            body = login_required(body)
            body = permissions_helpers.ensure_user_has_permissions(permissions_required)(body)

        return cls.create_mutation(
            mutation_class_name=mutation_class_name,
            description=description,
            arguments=arguments,
            return_type={
                output_name: cls.returns_id_list(django_graphql_type,
                                                    description=f"all the ids of the {django_type.__name__} models we have removed from the database")
            },
            body=body
        )

    @classmethod
    def generate_mutation_mark_inactive(cls, django_type: type, django_graphql_type: type,
                                 django_input_type: type,
                                 description: str = None, input_name: str = None,
                                 output_name: str = None,
                                 active_flag_name: str = None,
                                 permissions_required: List[str] = None,
                                mutation_class_name: Union[str, Callable[[str], str]] = None) -> type:
        """
        Create a mutation that simulate a deletes of a row stored in the database by setting the corresponding active flag to false.
        This usually set as inactive only the given row.
        We will generate a mutation that accepts a single array of integers, each representing the ids to delete.
        If an id is not present in the database, the mutation ignores it.
        The mutation returns the set of ids that were actually flagged as removed

        This method can already integrate graphene_jwt to authenticate and authorize users

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene package
        :param django_input_type: class deriving from DjangoInputObjectType from django graphene extras package
        :param description: description of the create mutation
        :param input_name: the name of the only mutation argument. If unspecified, it is the plural form of
            the camel case of the django_type
        :param output_name: the name of the only mutation return value. If unspecified, it is "removed"
        :param active_flag_name: name of the field in the associate djan go model corresponding to the active flag. If missing, it is "active"
        :param permissions_required: if absent, the mutation does not require authentication. If it is non null,
            the mutation needs authentication as well as all the permissions in input.
            When authenticating a mutation, an additional "token" argument is always added
        :param mutation_class_name: a function that generates the name of the mutation type. Input argument is django_type.__name__. The output is
            the mutation name to generate. The name is then converted into pascal case automatically. If left unspecified, it is "Create{django_type.__name__}".
            Can also be a string. Note that at the end, this pascal case name will be automatically converted by graphene into camel case.
        """

        primary_key_name = django_helpers.get_name_of_primary_key(django_type)
        if mutation_class_name is None:
            mutation_class_name = f"MarkInactive{django_type.__name__}"
        if hasattr(mutation_class_name, "__call__"):
            mutation_class_name = mutation_class_name(django_type.__name__)
        if active_flag_name is None:
            active_flag_name = "active"
        if description is None:
            description = f"""Allows you to remove a set of preexisting instances of {django_type.__name__} by marking them as inactive. 
                        If an object is not present in the database, we will skip the object deletion.
                        Object comparison is done by looking at the involved ids, each named {primary_key_name}.
                        The mutation yields a list of ids, representing the ones that have been removed from the
                        database.
                    """
            if permissions_required is not None:
                description += f"""Note that you need to authenticate your user in order to use this mutation.
                        The permission your user is required to have are: {', '.join(permissions_required)}. 
                        """
        if input_name is None:
            p = inflect.engine()
            input_name = p.plural(stringcase.camelcase(django_type.__name__))
        if output_name is None:
            output_name = "removed"

        def body(mutation_class, info, *args, **kwargs) -> any:
            id_list: List[int] = kwargs[input_name]

            result = []
            for i in id_list:
                obj = django_type.objects.find_only_or_None(pk=i)
                if obj is not None:
                    setattr(obj, active_flag_name, False)
                    obj.save()
                    result.append(getattr(obj, primary_key_name))

            return mutation_class(result)

        arguments = dict()
        arguments[input_name] = cls.argument_required_id_list(django_type.__name__)
        if permissions_required is not None:
            arguments["token"] = cls.argument_jwt_token()
            body = login_required(body)
            body = permissions_helpers.ensure_user_has_permissions(permissions_required)(body)

        return cls.create_mutation(
            mutation_class_name=mutation_class_name,
            description=description,
            arguments=arguments,
            return_type={
                output_name: cls.returns_id_list(django_graphql_type,
                    description=f"all the ids of the {django_type.__name__} models we have removed from the database")
            },
            body=body
        )

    # QUERY ARGUMENTS

    @classmethod
    def jwt_token(cls) -> graphene.String:
        return graphene.String(required=False, description=
            """jwt token used to authorize the request. 
            If left out, we will use the token present in the Authroization header
            """)

    @classmethod
    def required_id(cls, entity: Union[type, str] = None) -> graphene.ID:
        """
        The graphql query/mutation generates an id of  given entity
        """
        if entity is not None:
            if isinstance(entity, type):
                entity = entity.__name__
            desc = f"identifier uniquely representing a {entity} within the system"
        else:
            desc = f"Unique identifier representing the involved entity"
        return graphene.ID(required=True, description=desc)

    @classmethod
    def required_boolean(cls, description: str = None) -> graphene.Boolean:
        """
        A boolean, which needs to be specified
        """
        return graphene.Boolean(required=True)

    @classmethod
    def required_string(cls, description: str = None) -> graphene.String:
        """
        a reference of the value fo a field
        """
        return graphene.String(required=True, description=description)

    # MUTATION ARGUMENTS

    @classmethod
    def argument_required_id(cls, entity: Union[str, type] = None, description: str = None) -> graphene.Argument:
        """
        Unique identifier of an entity. Used within Argument metaclass for mutations

        :param entity: name of the class of the entity this id represents
        :param description: description of this argument
        """
        if entity is not None:
            if isinstance(entity, type):
                entity = entity.__name__
            description = f"identifier uniquely representing a {entity} within the system"
        else:
            description = f"Unique identifier representing the involved entity"
        return graphene.Argument(graphene.ID, required=True, description=description)

    @classmethod
    def argument_required_id_list(cls, entity: Union[type, str] = None, description: str = None) -> graphene.Argument:
        """
        Unique identifiers list of an entity. Used within Argument metaclass for mutations

        :param entity: name of the class of the entity this id represents
        :param description: description of the argument. it will be concatenated with the generated information
        """
        if entity is not None:
            if isinstance(entity, type):
                entity = entity.__name__
            desc = f"identifiers each uniquely representing a {entity} within the system."
        else:
            desc = f"Unique identifier list each representing an entity."
        if description is not None:
            desc += description
        return graphene.Argument(graphene.List(graphene.ID), required=True, description=desc)

    @classmethod
    def argument_required_string(cls, description: str = None) -> graphene.String:
        """
        a reference of the value fo a field. Used within Argument metaclass for mutations
        """
        return graphene.String(required=True, description=description)

    @classmethod
    def argument_required_input(cls, input_type: type, description: str = None) -> graphene.Argument:
        """
        a reference of the value od a field. Used within Argument metaclass for mutations

        :param input_type: class extending DjangoInputObjectType
        :param description: if present, the help text to show to graphiQL
        :return: argument of a mutation
        """
        if description is None:
            description = f"input of type {input_type._meta.model}"
        return graphene.Argument(input_type, required=True, description=description)

    @classmethod
    def argument_jwt_token(cls) -> graphene.String:
        return graphene.String(
            required=False,
            description="jwt token used to authorize the request. If left out, we will use the token present in the Authroization header"
        )

    # RETURN VALUES

    @classmethod
    def returns_id_list(cls, entity_type: Union[type, str], description: str = None) -> graphene.List:
        """
        A boolean, which tells if the mutation was successful or not

        :param entity_type: class extending models.Model
        :param description: description of the list
        :return: graphene type
        """
        if isinstance(entity_type, str):
            entity_name = entity_type
        elif isinstance(entity_type, type):
            entity_name = entity_type.__name__
        else:
            raise TypeError(f"invalid type {entity_type}!")
        return graphene.List(graphene.ID, required=True, description=f"{MUTATION_FIELD_DESCRIPTION}. List of {entity_name} ids. {description}")


    @classmethod
    def return_ok(cls, description: str = None) -> graphene.Boolean:
        """
        A boolean, which tells if the mutation was successful or not

        :param description: additional description for the query. It will be concatenated after the default description
        :return: graphene type
        """
        return graphene.Boolean(required=True, description=f"{MUTATION_FIELD_DESCRIPTION} True if the oepration was successful, false otherwise")

    @classmethod
    def returns_required_boolean(cls, description: str = None) -> graphene.Boolean:
        """
        A boolean, which needs to be always present

        :param description: additional description for the query. It will be concatenated after the default description
        :return: graphene type
        """
        return graphene.Boolean(required=True, description=f"{MUTATION_FIELD_DESCRIPTION} {description or ''}")

    @classmethod
    def returns_required_string(cls, description: str = None) -> graphene.String:
        """
        A strnig, which needs to be always present:

        :param description: additional description for the query. It will be concatenated after the default description
        :return: graphene type
        """
        return graphene.String(required=True, description=f"{MUTATION_FIELD_DESCRIPTION} {description or ''}")

    @classmethod
    def returns_nonnull(cls, return_type: type, description: str = None) -> graphene.Field:
        """
        tells the system that the mutation returns a non null value

        :param return_type: class extending DjangoObjectType.
        :param description: if present, the help text to show to graphiQL
        :return: return value of a mutation
        """
        if description is None:
            description = ""
        return graphene.Field(return_type, description=f"{MUTATION_FIELD_DESCRIPTION} {description}", required=True)

    @classmethod
    def returns_nonnull_list(cls, return_type: type, description: str = None) -> graphene.Field:
        """
        tells the system that the mutation returns a non null value

        :param return_type: class extending DjangoObjectType. We will return a list of such classes
        :param description: if present, the help text to show to graphiQL
        :return: return value of a mutation
        """
        if description is None:
            description = ""
        return graphene.Field(graphene.List(return_type), description=f"{MUTATION_FIELD_DESCRIPTION} {description}", required=True)