from typing import List, Tuple, Dict, Any, Callable, Union

import inspect
import graphene
import graphene_django
import inflect as inflect
import stringcase
import logging

from django.db.models import QuerySet
from graphene.types.unmountedtype import UnmountedType

from django_koldar_utils.django_toolbox import filters_helpers, django_helpers, auth_decorators
from koldar_utils.functions import python_helpers
from django_koldar_utils.graphql_toolsbox import graphql_decorators, error_codes
from django_koldar_utils.graphql_toolsbox.GraphQLAppError import GraphQLAppError
from django_koldar_utils.graphql_toolsbox.graphql_types import TDjangoModelType, TGrapheneType, TGrapheneArgument, \
    TGrapheneReturnType, TGrapheneQuery
from django_koldar_utils.graphql_toolsbox.scalars.ArrowDateScalar import ArrowDateScalar
from django_koldar_utils.graphql_toolsbox.scalars.ArrowDateTimeScalar import ArrowDateTimeScalar
from django_koldar_utils.graphql_toolsbox.scalars.ArrowDurationScalar import ArrowDurationScalar

MUTATION_FIELD_DESCRIPTION = "Mutation return value. Do not explicitly use it."
"""
A prefix to put to every mutation return value"""

LOG = logging.getLogger(__name__)



class GraphQLHelper(object):
    """
    Class used to generate relevant queries and mutations fields for graphql_toolsbox
    """

    # INFO

    @classmethod
    def is_field_id(cls, field_type: Union[graphene.ObjectType, TGrapheneReturnType, TGrapheneType]) -> bool:
        """

        :param field_type: field to check. It can also be an instance of field
        :return: true if the graphene field represents an ID, false otherwise
        """
        field_type = GraphQLHelper.get_actual_type_from_field(field_type)
        return issubclass(field_type, graphene.ID, graphene.GlobalID)

    @classmethod
    def is_field_non_primitive(cls, field_type: Union[graphene.ObjectType, TGrapheneReturnType, TGrapheneType]) -> bool:
        """
        :param field_type: field to check. It can also be an instance of field
        :return: true if the graphene field represents a complex input, false otherwise
        """
        field_type = GraphQLHelper.get_actual_type_from_field(field_type)
        return issubclass(field_type, graphene.InputObjectType)

    @classmethod
    def get_actual_type_from_field(cls, field: Union[graphene.ObjectType, TGrapheneReturnType, TGrapheneType]) -> TGrapheneReturnType:
        """
        Recursively query the field in order to find its basic representation. For example
        the basic representation of "Field(ID!)" is "ID"

        :param field: either a field instance (pretty rare but possible) or a type repersenting a field
        :return: the field representing the field
        """
        if isinstance(field, graphene.ObjectType):
            return GraphQLHelper.get_actual_type_from_field(type(field))
        if isinstance(field, graphene.NonNull):
            return GraphQLHelper.get_actual_type_from_field(field.of_type)
        # if isinstance(field, UnmountedType):
        #     return GraphQLHelper.get_actual_type_from_field(field.type)
        if isinstance(field, graphene.Field):
            return GraphQLHelper.get_actual_type_from_field(field.type)
        if isinstance(field, graphene.Argument):
            return GraphQLHelper.get_actual_type_from_field(field.type)
        else:
            return field

    @classmethod
    def is_representing_input_argument(cls, field: graphene.ObjectType) -> bool:
        """
        :param field: graphene parameter to check
        :return: true if this graphene field argument represents a graphql input
        """
        if isinstance(field, graphene.InputObjectType):
            return True
        if inspect.isclass(field) and issubclass(field, graphene.InputObjectType):
            return True
        if isinstance(field, graphene.NonNull):
            return GraphQLHelper.is_representing_input_argument(field.of_type)
        if isinstance(field, graphene.Argument):
            return GraphQLHelper.is_representing_input_argument(field.type)
        if isinstance(field, graphene.Field):
            return GraphQLHelper.is_representing_input_argument(field.type)
        return False

    # QUERY MUTATION CONSTRUCTION


    @classmethod
    def create_simple_query(cls, return_type: type, arguments: Dict[str, Any],
                            description: str = None) -> graphene.Field:
        """
        Creates a graphql_toolsbox query. It is simple because you need to fill out the arguments and hte other stuff by yourself.
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
                                          description: str = None, token_name: str = None) -> graphene.Field:
        """
        Like create_simple_query but we implicitly add a JWT token in the arguments of the query named "token"

        :: code-block:: python
            permission = create_authenticated_query(PermissionGraphQLType, arguments=dict(id=AbstractQuery.required_id("system permissions")), description="fethc a given permission")

        :param return_type: a type extendintg DjangoGraphQLObjectType
        :param arguments: dictionary of query arguments.
        :param description: help text to show in the graphQL GUI
        :param token_name: name of the token used to authenticate query. Ifl eft missing, it is "token"
        :return query value. You still need to implement "def resolve_X(self, info, **kwargs):" method within the class
            containing the body of the query
        """
        if token_name is None:
            token_name = "token"
        arguments[token_name] = cls.jwt_token()
        return cls.create_simple_query(return_type=return_type, arguments=arguments, description=description)

    @classmethod
    def create_authenticated_list(cls, django_type: type, django_graphql_type: type, get_all_filter: any,
                                  permissions_required: List[str],
                                  query_class_name: Union[str, Callable[[type, type], str]] = None,
                                  output_name: Union[str, Callable[[str, any], str]] = None,
                                  token_name: str = None) -> type:
        """
        Create an authentication query allowing you to to list all the content of a particular model satisfying the specified
        filter. The return type of this query is always a list.

        :param django_type: a type representing the models.Model subclass
        :param django_graphql_type: a type representing the DjangoObjectType of the corresponding django_type
        :param get_all_filter: django_toolbox query filter that implements the output of the query
        :param permissions_required: set of permissions the authenticated query needs to satisfy
        :param token_name: name of the token used to authenticate the query. If left missing it isd "token"
        :return: type representing the graphene_toolbox query list.
        """
        read_all = cls.generate_query_from_filter_set(
            return_single=False,
            django_type=django_type,
            django_graphql_type=django_graphql_type,
            permissions_required=permissions_required,
            filterset_type=get_all_filter,
            query_class_name=query_class_name,
            output_name=output_name,
            token_name=token_name
        )
        return read_all

    @classmethod
    def create_authenticated_list_from_callable(cls, django_type: TDjangoModelType, django_graphql_type: TGrapheneType,
                                  permissions_required: List[str],
                                  query_description: str = None,
                                  query_arguments: Dict[str, TGrapheneArgument] = None,
                                  query_callable: Callable[[QuerySet, any], Union[QuerySet, any]] = None,
                                  query_class_name: Union[str, Callable[[type, type], str]] = None,
                                  output_name: Union[str, Callable[[str, any], str]] = None,
                                  token_name: str = None) -> type:
        """
        Create an authentication query allowing you to to list all the content of a particular model satisfying the specified
        filter. The return type of this query is always a list.

        :param django_type: a type representing the models.Model subclass
        :param django_graphql_type: a type representing the DjangoObjectType of the corresponding django_type
        :param get_all_filter: django_toolbox query filter that implements the output of the query
        :param permissions_required: set of permissions the authenticated query needs to satisfy
        :param token_name: name of the token used to authenticate the query. If left missing it isd "token"
        :return: type representing the graphene_toolbox query list.
        """
        read_all = cls.generate_query_from_lambda(
            return_single=False,
            django_type=django_type,
            django_graphql_type=django_graphql_type,
            permissions_required=permissions_required,
            query_arguments=query_arguments,
            query_description=query_description,
            query_callable=query_callable,
            query_class_name=query_class_name,
            output_name=output_name,
            token_name=token_name
        )
        return read_all

    @classmethod
    def create_authenticated_query(cls, query_class_name: str, description: str, arguments: Dict[str, type],
                                   return_type: type, body: Callable, permissions_required: List[str],
                                   add_token: bool = False, token_name: str = None) -> type:
        """
        Create a graphQL query. Decorators on body will be considered

        :param query_class_name: name of the query generated
        :param description: description of the query
        :param arguments: list of arguments in input of the query. It is a dictioanry where the values are graphene_toolbox
            types (e.g., graphene_toolbox.String). If inputting a complex type, use graphene_toolbox.Argument.
        :param return_type: return type (ObjectType) of the query.
        :param body: a callable specifiying the code of the query. The first is the query class isntance.
            Info provides graphql_toolsbox context. the rest are the query arguments.
            You need to return the query value
        :param permissions_required: list fo permissions required to be satisfied in order for fully using the function
        :param add_token: if set, we will add an optional token as parameter for the query
        :param token_name: name of the token (if added). If left missing, it is "token"
        """

        description = description + f"""The query requires authentication. Specifically, it requires the following permissions:
        {', '.join(permissions_required)}.
        """
        if token_name is None:
            token_name = "token"
        if add_token:
            arguments[token_name] = cls.argument_jwt_token()
        return cls._create_query(
            query_class_name=query_class_name,
            description=description,
            arguments=arguments,
            output_name=stringcase.camelcase(query_class_name),
            return_type=return_type,
            body=auth_decorators.graphql_ensure_login_required()(
                auth_decorators.graphql_ensure_user_has_permissions(permissions_required)(body))
        )

    @classmethod
    def _create_query(cls, query_class_name: str, description: str, arguments: Dict[str, type],
                     output_name: str, return_type: type, body: Callable) -> type:
        """
        Create a graphQL query. Decorators on body will be considered

        :param query_class_name: name of the query generated
        :param description: description of the query
        :param arguments: list of arguments in input of the query. It is a dictioanry where the values are graphene_toolbox
            types (e.g., graphene_toolbox.String). If inputting a complex type, use graphene_toolbox.Argument.
        :param output_name: name of the output variable in the graphQL language
        :param return_type: return type (ObjectType) of the . Do not add here a graphene_toolbox.Field type!
        :param body: a callable specifiying the code of the query. The first is the query class isntance. Info provides graphql_toolsbox context. the rest are the query arguments. You need to return the query value
        """

        # @graphql_subquery
        # class Query(graphene_toolbox.ObjectType):
        #     question = graphene_toolbox.Field(
        #         QuestionType,
        #         foo=graphene_toolbox.String(),
        #         bar=graphene_toolbox.Int()
        #     )
        #
        #     def resolve_question(root, info, foo, bar):
        #         # If `foo` or `bar` are declared in the GraphQL query they will be here, else None.
        #         return Question.objects.filter(foo=foo, bar=bar).first()

        assert query_class_name is not None, "Query class name is None"
        assert all(map(lambda x: x is not None, arguments.keys())), f"Some arguments of {query_class_name} are None"
        assert output_name is not None, f"output of {query_class_name} is None"
        assert return_type is not None, f"return type of {query_class_name} is None"
        assert description is not None, f"description of {query_class_name} is None"
        assert (not inspect.isclass(return_type)) or (issubclass(return_type, (graphene.Scalar, graphene.ObjectType, graphene_django.DjangoObjectType))), \
            f"return type \"{return_type}\" of \"{query_class_name}\" cannot be a type subclass graphene_toolbox.Field, but needs to be a plain ObjectType!"
        assert ((inspect.isclass(return_type)) or (isinstance(return_type, (graphene.List, graphene.Field)))), \
            f"return type \"{return_type}\" of \"{query_class_name}\" cannot be an instanc deriving graphene_toolbox.Field, but needs to be a plain ObjectType!"

        def perform_query(root, info, *args, **kwargs) -> any:
            if root is None:
                root = query_class
            result = body(root, info, *args, **kwargs)
            # check output soundness. It is important because debuggin this type of error is quite difficult.
            if isinstance(result, list):
                if not isinstance(return_type, graphene.List):
                    raise TypeError(
                        f"Query generated a list ({result}), but the query expected to return a {return_type}")
            else:
                # check if it is field
                # if isinstance(result, graphene_toolbox.Field):
                #     result = result.type

                if isinstance(result, root):
                    # the return value is the same as the root class. (e.g., CookiePolicy and CookiePolicy instance
                    pass
                elif not isinstance(result, return_type):
                    # maybe the result is AuthUser and the return type is AuthUserGraphQLType
                    # in case of CookiePolicy and String. The problem here is that return type is
                    # just a field of the return class some "_meta" classes (e.g., ScalarOptions) do not
                    # have a "model" attribute, so we need to filter it
                    if hasattr(return_type._meta, "model"):
                        if not isinstance(result, return_type._meta.model):
                            raise TypeError(f"""Expected body of query {query_class_name} to return either 
                                {return_type.__name__} or {return_type._meta.model.__name__}, but instead it 
                                returned {type(result).__name__}""")
            return result

        if isinstance(return_type, graphene.Field):
            # needed otherwise graphene_toolbox.schema will raise an exception
            return_type = return_type.type

        query_class = type(
            query_class_name,
            (graphene.ObjectType,),
            {
                "__doc__": description,
                f"resolve_{output_name}": perform_query,
                output_name: graphene.Field(return_type, args=arguments, description=description),
            }
        )
        # Apply decorator to auto detect queries
        decorated_query_class = graphql_decorators.graphql_subquery(query_class)

        return decorated_query_class



    @classmethod
    def generate_query_from_queryset_filter(cls,
                                            django_type: TDjangoModelType,
                                            query_class_name: str,
                                            description: str,
                                            output_name: str,
                                            return_multipler: str,
                                            queryset_filter: Callable[[QuerySet, TGrapheneQuery, any, List[any], Dict[str, any]], QuerySet],
                                            arguments: Dict[str, TGrapheneArgument],
                                            return_type: TGrapheneType,
                                            body_decorator: Callable[[TDjangoModelType, str, Dict[str, TGrapheneArgument], TGrapheneType], Callable],
                                            ) -> Tuple[TGrapheneQuery, Dict[str, TGrapheneType]]:
        """
        Generate a graphql query reading the database. This is the main method that can be used to generate read queries
        easily

        :param django_type: type of the model this query will base its django filter on
        :param query_class_name: name of the type to generate
        :param description: description of the query to generate
        :param output_name: name of the output field generated by this query
        :param return_multipler: can be "optional", "single" or "multi". "Single" means that the query will return
            exactly one element, "optional" means that it can return at most one,
            while "multi" means that the query can return at most n (possible 0).
        :param queryset_filter: a callable representing how the output will be computed. Arguments are:
         - initial query set to filter
         - query class type
         - info graphql argument
         - *args graphql argument
         - **kwargs graphql argument
        :param arguments: arguments of the graphql query
        :return_type: type that is returned by the query. If return_multipler is "single" or "optional", it is the graphene
            type of the element returned by the query. if return_multipler is "multi", it is a single element of the list
            generated by the query.
        :param body_decorator: a function that yield a decorator that will be applied to the actual graphql query body content.
            You can use it to alter its behaviour. The decorator factory signature needs to be:
             - django_type
             - query_class_name
             - arguments
             - return_type
             - return: decorator function
        :return: a tuple where the first item is the class representing this query while the second is the return type
            of the query
        """

        def body(mutation_class, info, *args, **kwargs) -> any:
            qs = django_type._default_manager.all()
            qs = queryset_filter(qs, mutation_class, info, list(args), kwargs)
            result = list(qs)

            if return_multipler == "single":
                if len(result) != 1:
                    raise ValueError(f"We expected the query to yield a single value, but got {len(result)}!")
                return mutation_class(result[0])
            elif return_multipler == "optional":
                if len(result) > 1:
                    raise ValueError(f"We expected the query to yield at most a value, but got {len(result)}!")
                result = result[0] if len(result) > 0 else None
                return mutation_class(result)
            elif return_multipler == "multi":
                return mutation_class(result)
            else:
                raise ValueError(f"Invalid multipler '{return_multipler}'!")

        if return_multipler == "single":
            return_type = GraphQLHelper.returns_nonnull(return_type)
        elif return_multipler == "optional":
            return_type = GraphQLHelper.return_nullable(return_type)
        elif return_multipler == "multi":
            return_type = GraphQLHelper.returns_nonnull_list(return_type)
        else:
            raise ValueError(f"Invalid multipler '{return_multipler}'!")

        result = GraphQLHelper._create_query(
            query_class_name=query_class_name,
            description=description,
            arguments=arguments,
            output_name=output_name,
            return_type=return_type,
            body=body_decorator(django_type, query_class_name, arguments, return_type)(body)
        )

        return result, {output_name: result.cls._meta.fields[output_name]}


    @classmethod
    def generate_query_from_lambda(cls, django_type: TDjangoModelType, django_graphql_type: TGrapheneType,
                                       return_single: bool = False,
                                       query_description: str = None,
                                       query_arguments: Dict[str, TGrapheneArgument] = None,
                                       query_callable: Callable[[QuerySet, Dict[str, any]], Union[QuerySet, any]] = None,
                                       query_class_name: Union[str, Callable[[str], str]] = None,
                                       permissions_required: List[str] = None, output_name: str = None,
                                       query_output_return_type: TGrapheneReturnType = None,
                                       token_name: str = None) -> TGrapheneQuery:
        """
        generate a single graphQL query reprensented by the given callable


        .. :code-block: python

            generate_query_from_lambda(
                django_type=Author,
                django_graphql_type=AuthorGraphQL,
                return_single=True,
                query_description="find a single author by name",
                query_arguments=dict(
                    id=graphene_toolbox.ID(required=True),
                ),
                query_callable=lambda qs, id: qs.filter(pk=id)
                query_class_name="FindAuthorById",
                permissions_required=["can_view_author"]
            )

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene_toolbox package
        :param query_description: description of the query callable
        :param query_callable: the function used to filter queries. First input parameter is the query set from objects.all()
            while the seocndi is dictionary containing all the graphql_toolsbox query parameters. Make sure the parameter name
            corresponds to the query argument.
        :param return_single: if True, you know that the query will return a single result. Otherwise it will return
            a list. Ignored if "query_output_return_type" is set
        :param permissions_required: list fo permissions that the autneticatd user needs to satisfy if she wants to gain
            access to the query. If left None, the query won't be authenticated at all
        :param output_name: name of the return value fo the qiery. It is also the name of the query altogether
        :param query_output_return_type: the type of a return value field in the query output storing the output of the query.
            Ifl eft unspecified it isi either a django_graphql_type or or a list of django_graphql_type. However, if you
            need a different output tyype (e.g., a different type or a dictionary), you can set this field.
            By doing so, "return_single" will be ignored. Notice that you need to make sure the correct type is
            returned by "query_callable", if this is the case.
        :param token_name: name of the token used to authenticate the query
        :return: a graphql_toolsbox query type representing a query to perform on the system
        """

        def default_query_callable(query_param: Dict[str, any], query_set: QuerySet) -> Union[QuerySet, any]:
            return query_set

        p = inflect.engine()

        django_type_str = stringcase.pascalcase(django_type.__name__)
        if token_name is None:
            token_name = "token"
        if query_callable is None:
            query_callable = default_query_callable
        if query_description is None:
            query_description = f"Get all the {django_type_str} involved"
        if query_arguments is None:
            query_arguments = dict()

        # QUERY NAME
        if query_class_name is None:
            query_class_name = stringcase.pascalcase(django_type_str)
        else:
            if python_helpers.is_function(query_class_name):
                # function
                query_class_name = query_class_name(django_type_str)
            elif isinstance(query_class_name, str):
                pass
            else:
                raise TypeError(f"Invalid type {type(query_class_name)}!")

        # GRAPHQL DESCRIPTION
        description_multiplier = "a single" if return_single else "all the"
        description = f"""This query allow the user to retrieve {description_multiplier} active {django_type.__name__} within the system
            satisfying the following given condition: {query_description}.
            """
        if permissions_required is not None:
            description += f"""The query needs authentication in order to be run. The permissions required 
                by the backend in order to properly work are: {', '.join(permissions_required)}"""

        # GRAPHQL QUERY OUTPUT FIELD NAME
        if output_name is None:
            output_name = f"{stringcase.camelcase(django_type.__name__)}QueryOutcome"

        # GRAPHQL QUERY OUTPUT FIELD
        if query_output_return_type is None:
            return_single_meaningful = True
            # return type
            if return_single:
                query_return_type = django_graphql_type
            else:
                query_return_type = graphene.List(django_graphql_type)
        else:
            return_single_meaningful = False
            query_return_type = query_output_return_type

        # GRAPHQL QUERY ARGUMENTS
        # the query arguments are all the single filters available in the filterset
        arguments: Dict[str, type] = dict()
        for field_name, field in query_arguments.items():
            arguments[field_name] = field

        # GRAPHQL BODY
        def body(query_class, info, *args, **kwargs) -> any:
            # query actual parameters. May be somethign of sort: {'username': 'alex', 'status': '1'}
            # we need to remove the token argument (if present)
            query_actual_parameters = {k: kwargs[k] for k in arguments if k in kwargs and k not in (token_name,)}
            # see https://github.com/carltongibson/django-filter/blob/main/tests/test_filtering.py
            qs = django_type._default_manager.all()
            output = query_callable(qs, **query_actual_parameters)
            # return output
            if not return_single_meaningful:
                return output
            else:
                if return_single:
                    return output
                else:
                    return list(output)

        # GRAPHQL PERMISSIONS
        if permissions_required is not None:
            # add token and authentication decorators
            arguments[token_name] = cls.argument_jwt_token()
            body = auth_decorators.graphql_ensure_login_required()(body)
            body = auth_decorators.graphql_ensure_user_has_permissions(permissions_required)(body)

        result = cls._create_query(
            query_class_name=query_class_name,
            description=description,
            arguments=arguments,
            output_name=output_name,
            return_type=query_return_type,
            body=body
        )
        return result

    @classmethod
    def generate_query_from_filter_set(cls, django_type: type, django_graphql_type: type, filterset_type: type,
                                       return_single: bool,
                                       query_class_name: Union[str, Callable[[str, str], str]] = None,
                                       permissions_required: List[str] = None, output_name: str = None,
                                       token_name: str = None) -> type:
        """
        generate a single graphQL query reprensented by the given filter_set

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene_toolbox package
        :param return_single: if True, you know that the query will return a single result. Otherwise it will return a list
        :param filterset_type: filterset that will be used to generate the query
        :param permissions_required: list fo permissions that the autneticatd user needs to satisfy if she wants to gain
            access to the query. If left None, the query won't be authenticated at all
        :param output_name: name of the return value fo the qiery. It is also the name of the query altogether
        :param token_name: name of the token used to authenticate the query
        """

        p = inflect.engine()

        filterset_name = filterset_type.__name__
        if filterset_name.endswith("Filter"):
            filterset_name = filterset_name[:-len("Filter")]
        if token_name is None:
            token_name = "token"
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
            # we need to remove the token argument (if present)
            query_actual_parameters = {k: kwargs[k] for k in arguments if k in kwargs and k not in (token_name,)}
            # see https://github.com/carltongibson/django-filter/blob/main/tests/test_filtering.py
            qs = django_type.objects.all()
            f = filterset_type(query_actual_parameters, queryset=qs)
            if return_single:
                return f.qs
            else:
                return list(f.qs)

        if permissions_required is not None:
            # add token and authentication decorators
            arguments[token_name] = cls.argument_jwt_token()
            body = auth_decorators.graphql_ensure_login_required()(body)
            body = auth_decorators.graphql_ensure_user_has_permissions(permissions_required)(body)

        result = cls._create_query(
            query_class_name=query_class_name,
            description=description,
            arguments=arguments,
            output_name=output_name,
            return_type=query_return_type,
            body=body
        )
        return result

    @classmethod
    def create_mutation(cls, mutation_class_name: str, description: str, arguments: Dict[str, any],
                        return_type: Dict[str, any], body: Callable) -> type:
        """
        Create a generic mutation

        :param mutation_class_name: name of the subclass of graphene_toolbox.Mutation that represents ths mutation
        :param description: description of the mutation. This will be shown in graphiQL
        :param arguments: argument fo the mutation. The values are set as Helper.argument_x
        :param return_type: values that the mutation will return
        :param body: function containign the mutation. return value is any.
            - 1 parameter is the mutation class name;
            - 2 parameter is info;
            - Then you can have the same parameters as the arguments (as input);
            - other parmaeters should be put in **args, **kwargs;
        """

        assert mutation_class_name is not None, "mutation class name is none"
        assert all(map(lambda x: x is not None, arguments.keys())), f"argument of {mutation_class_name} are none"
        assert return_type is not None, "return type is None. This should not be possible"
        assert "mutate" not in return_type.keys(), f"mutate in return type of class {mutation_class_name}"
        assert all(
            map(lambda x: x is not None, return_type.keys())), f"some return value of {mutation_class_name} are None"
        assert description is not None, f"description of {mutation_class_name} is None"
        assert isinstance(arguments, dict), f"argument is not a dictionary"
        assert isinstance(list(arguments.keys())[0], str), f"argument keys are not strings!"

        mutation_class_meta = type(
            "Arguments",
            (object,),
            arguments
        )

        def mutate(root, info, *args, **kwargs) -> any:
            if root is None:
                root = mutation_class
            return body(root, info, *args, **kwargs)

        LOG.info(f"Argument are {arguments}")
        LOG.info(
            f"Creating mutation={mutation_class_name}; metaclass={mutation_class_meta.__name__}; arguments keys={','.join(arguments.keys())}; return={', '.join(return_type.keys())}")
        mutation_class = type(
            mutation_class_name,
            (graphene.Mutation,),
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

    @classmethod
    def create_authenticated_mutation(cls, mutation_class_name: str, description: str, arguments: Dict[str, any],
                                      return_type: Dict[str, any], body: Callable, required_permissions: List[str],
                                      token_name: str = None) -> type:
        """
        Create a generic mutation which requires authentication. Authentication is automatically added

        :param mutation_class_name: name of the subclass of graphene_toolbox.Mutation that represents ths mutation
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
        :param token_name: name of the token of the authenticated mutation
        :return: class representing the mutation
        """

        if token_name is None:
            token_name = "token"
        mutation_class_meta = type(
            "Arguments",
            (object,),
            {token_name: cls.argument_jwt_token(), **arguments}
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
                "mutate": auth_decorators.graphql_ensure_login_required()(
                    auth_decorators.graphql_ensure_user_has_permissions(required_permissions)(mutate))
            }
        )
        # Apply decorator to auto detect mutations
        mutation_class = graphql_decorators.graphql_submutation(mutation_class)

        return mutation_class

    # @classmethod
    # def generate_mutation_create(cls, django_type: type, django_graphql_type: type, django_input_type: type,
    #                              active_flag_name: str = None, fields_to_check: List[str] = None,
    #                              description: str = None, input_name: str = None, output_name: str = None,
    #                              permissions_required: List[str] = None,
    #                              mutation_class_name: Union[str, Callable[[str], str]] = None,
    #                              token_name: str = None) -> type:
    #     """
    #     Create a mutation that adds a new element in the database.
    #     We will generate a mutation that accepts a single input parameter. It checks if the input is not already present in the database and if not, it adds it.
    #     The returns the data added in the database.
    #     This method can already integrate graphene_jwt to authenticate and authorize users
    #
    #     :param django_type: class deriving from models.Model
    #     :param django_graphql_type: class deriving from DjangoObjectType of graphene_toolbox package
    #     :param django_input_type: class deriving from DjangoInputObjectType from django_toolbox graphene_toolbox extras package
    #     :param active_flag_name: name fo the active flag
    #     :param fields_to_check: field used to check uniquness of the row. If missing, we will populate them with all the unique fields
    #     :param description: description of the create mutation
    #     :param input_name: the name of the only mutation argument. If unspecified, it is the camel case of the django_type
    #     :param output_name: the name of the only mutation return value. If unspecified, it is the camel case of the django_type
    #     :param permissions_required: if absent, the mutation does not require authentication. If it is non null,
    #         the mutation needs authentication as well as all the permissions in input.
    #         When authenticating a mutation, an additional "token" argument is always added
    #     :param mutation_class_name: a function that generates the name of the mutation type. Input argument is django_type.__name__. The output is
    #         the mutation name to generate. The name is then converted into pascal case automatically. If left unspecified, it is "Create{django_type.__name__}".
    #         Can also be a string. Note that at the end, this pascal case name will be automatically converted by graphene_toolbox into camel case.
    #     :param token_name: name of the token used to authenticate the mutation. If None it is "token"
    #     """
    #
    #     if token_name is None:
    #         token_name = "token"
    #     if mutation_class_name is None:
    #         mutation_class_name = f"Create{django_type.__name__}"
    #     if active_flag_name is None:
    #         active_flag_name = "active"
    #     if fields_to_check is None:
    #         # fetch all the unique fields
    #         fields_to_check = list(django_helpers.get_unique_field_names(django_type))
    #     if description is None:
    #         description = f"""Allows you to create a new instance of {django_type.__name__}.
    #             If the object is already present we throw an exception.
    #             We raise an exception if we are able to find a row in the database with the same fields: {', '.join(fields_to_check)}.
    #         """
    #         if permissions_required is not None:
    #             description += f"""Note that you need to authenticate your user in order to use this mutation.
    #             The permission your user is required to have are: {', '.join(permissions_required)}.
    #             """
    #     if input_name is None:
    #         input_name = stringcase.camelcase(django_type.__name__)
    #     if output_name is None:
    #         output_name = stringcase.camelcase(django_type.__name__)
    #     if hasattr(mutation_class_name, "__call__"):
    #         # if create_mutation_name is a function, call it
    #         mutation_class_name = mutation_class_name(django_type.__name__)
    #
    #     def body(mutation_class, info, *args, **kwargs) -> any:
    #         input = kwargs[input_name]
    #         d = dict()
    #         for f in fields_to_check:
    #             d[f] = getattr(input, f)
    #         #
    #         d[active_flag_name] = True
    #         if django_type.objects.has_at_least_one(**d):
    #             raise GraphQLAppError(error_codes.OBJECT_ALREADY_PRESENT, object=django_type.__name__, values=d)
    #         # create argumejnt and omits the None values
    #         create_args = {k: v for k, v in dict(input).items() if v is not None}
    #
    #         result = django_type.objects.create(**create_args)
    #         if result is None:
    #             raise GraphQLAppError(error_codes.CREATION_FAILED, object=django_type.__name__, values=create_args)
    #         return mutation_class(result)
    #
    #     arguments = dict()
    #     arguments[input_name] = cls.argument_required_input(django_input_type,
    #                                                         description="The object to add into the database. id should not be populated. ")
    #     if permissions_required is not None:
    #         arguments[token_name] = cls.argument_jwt_token()
    #         body = auth_decorators.graphql_ensure_login_required()(body)
    #         body = auth_decorators.graphql_ensure_user_has_permissions(permissions_required)(body)
    #
    #     return cls.create_mutation(
    #         mutation_class_name=str(mutation_class_name),
    #         description=description,
    #         arguments=arguments,
    #         return_type={
    #             output_name: cls.returns_nonnull(django_graphql_type,
    #                                              description=f"the {django_type.__name__} just added into the database")
    #         },
    #         body=body
    #     )

    @classmethod
    def generate_mutation_update_primitive_data(cls, django_type: type, django_graphql_type: type,
                                                django_input_type: type,
                                                description: str = None, input_name: str = None,
                                                active_flag_name: str = None, output_name: str = None,
                                                permissions_required: List[str] = None,
                                                mutation_class_name: Union[str, Callable[[str], str]] = None,
                                                token_name: str = None) -> type:
        """
        Create a mutation that revise a previously added element in the database to a newer version.
        This mutation updates only the primitive fields within the entity, jnot the relationships.
        We will generate a mutation that accepts 2 input parameters. The first is the id of the entry to alter while the second is the data to set.
        It checks if the input is not already present in the database. If not it generates an exception.
        The function  returns the data that is persisted in the database after the call.
        This method can already integrate graphene_jwt to authenticate and authorize users

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene_toolbox package
        :param django_input_type: class deriving from DjangoInputObjectType from django_toolbox graphene_toolbox extras package
        :param django_input_list_type: class derivigin from DjangoInputObjectType which repersents a list of inputs
        :param description: description of the create mutation
        :param input_name: the name of the only mutation argument. If unspecified, it is the camel case of the django_type
        :param output_name: the name of the only mutation return value. If unspecified, it is the camel case of the django_type
        :param permissions_required: if absent, the mutation does not require authentication. If it is non null,
            the mutation needs authentication as well as all the permissions in input.
            When authenticating a mutation, an additional "token" argument is always added
        :param mutation_class_name: a function that generates the name of the mutation type. Input argument is django_type.__name__. The output is
            the mutation name to generate. The name is then converted into pascal case automatically. If left unspecified, it is "Create{django_type.__name__}".
            Can also be a string. Note that at the end, this pascal case name will be automatically converted by graphene_toolbox into camel case.
        :param token_name: name of the token used to authenticate the mutation
        """

        primary_key_name = django_helpers.get_name_of_primary_key(django_type)
        if active_flag_name is None:
            active_flag_name = "active"
        if token_name is None:
            token_name = "token"
        if mutation_class_name is None:
            mutation_class_name = f"UpdatePrimitive{django_type.__name__}",
        if description is None:
            description = f"""Allows you to update a previously created new instance of {django_type.__name__}. 
                    If the object is already present we throw an exception.
                    We raise an exception if we are able to find a row in the database with the same primary key: {primary_key_name}.
                    With this mutation, it is possible to alter only the primitive fields belonging to the entity.
                    If the model instance is not active, we will do nothing. Every field which is left missing, is skipped.
                    In other words, association between models as well as pruimary key cannot be altered with this mutation.
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
            d[active_flag_name] = True
            if not django_type.objects.has_at_least_one(**d):
                raise GraphQLAppError(error_codes.OBJECT_NOT_FOUND, object=django_type.__name__, values=d)
            # create argument and omits the None values

            result = django_type.objects.find_only_or_fail(**d)
            input_as_dict = dict(input)
            for f in django_helpers.get_primitive_fields(django_type):
                name = f.attname
                if (not f.is_relation) and (name in input_as_dict) and (input_as_dict[name] is not None):
                    # we ignore fields that are relations
                    setattr(result, name, input_as_dict[name])
            result.save()

            return mutation_class(result)

        arguments = dict()
        arguments[primary_key_name] = cls.argument_required_id(django_type.__name__)
        arguments[input_name] = cls.argument_required_input(django_input_type,
                                                            description="The object that will update the one present in the database.")
        if permissions_required is not None:
            arguments[token_name] = cls.argument_jwt_token()
            body = auth_decorators.graphql_ensure_login_required()(body)
            body = auth_decorators.graphql_ensure_user_has_permissions(permissions_required)(body)

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
                                         mutation_class_name: Union[str, Callable[[str], str]] = None,
                                         token_name: str = None) -> type:
        """
        Create a mutation that deletes a row stored in the database. Depending on the on_delete, this may lead to the removal of other dependant rows
        We will generate a mutation that accepts a single array of integers, each representing the ids to delete.
        If an id is not present in the database, the mutation ignores it.
        The mutation returns the set of ids that were actually removed from the database.

        This method can already integrate graphene_jwt to authenticate and authorize users

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene_toolbox package
        :param django_input_type: class deriving from DjangoInputObjectType from django_toolbox graphene_toolbox extras package
        :param description: description of the create mutation
        :param input_name: the name of the only mutation argument. If unspecified, it is the plural form of
            the camel case of the django_type
        :param output_name: the name of the only mutation return value. If unspecified, it is "removed"
        :param permissions_required: if absent, the mutation does not require authentication. If it is non null,
            the mutation needs authentication as well as all the permissions in input.
            When authenticating a mutation, an additional "token" argument is always added
        :param mutation_class_name: a function that generates the name of the mutation type. Input argument is django_type.__name__. The output is
            the mutation name to generate. The name is then converted into pascal case automatically. If left unspecified, it is "Create{django_type.__name__}".
            Can also be a string. Note that at the end, this pascal case name will be automatically converted by graphene_toolbox into camel case.
        :param token_name: name of the token. If left missing, it is "token"
        """

        primary_key_name = django_helpers.get_name_of_primary_key(django_type)
        if token_name is None:
            token_name = "token"
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
            arguments[token_name] = cls.argument_jwt_token()
            body = auth_decorators.graphql_ensure_login_required()(body)
            body = auth_decorators.graphql_ensure_user_has_permissions(permissions_required)(body)

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
                                        mutation_class_name: Union[str, Callable[[str], str]] = None,
                                        token_name: str = None) -> type:
        """
        Create a mutation that simulate a deletes of a row stored in the database by setting the corresponding active flag to false.
        This usually set as inactive only the given row.
        We will generate a mutation that accepts a single array of integers, each representing the ids to delete.
        If an id is not present in the database, the mutation ignores it.
        The mutation returns the set of ids that were actually flagged as removed

        This method can already integrate graphene_jwt to authenticate and authorize users

        :param django_type: class deriving from models.Model
        :param django_graphql_type: class deriving from DjangoObjectType of graphene_toolbox package
        :param django_input_type: class deriving from DjangoInputObjectType from django_toolbox graphene_toolbox extras package
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
            Can also be a string. Note that at the end, this pascal case name will be automatically converted by graphene_toolbox into camel case.
        :param token_name: name of the token used to authenticate the mutation. If left missing, it is "token"
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
        if token_name is None:
            token_name = "token"

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
            arguments[token_name] = cls.argument_jwt_token()
            body = auth_decorators.graphql_ensure_login_required()(body)
            body = auth_decorators.graphql_ensure_user_has_permissions(permissions_required)(body)

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

    # Graphene Object is

    # QUERY ARGUMENTS AND DJANGO GRAPHQL TYPE DEFINITION

    @classmethod
    def jwt_token(cls) -> graphene.String:
        return graphene.String(required=False, description=
        """jwt token used to authorize the request. 
            If left out, we will use the token present in the Authorization header. 
            """)

    @classmethod
    def required_id(cls, entity: Union[type, str] = None, description: str = None) -> graphene.ID:
        """
        The graphql_toolsbox query/mutation generates an id of  given entity

        :param entity: entity whose id we need to store. Can be either a type or a string. The field is only used for
        documentation, not for actual code
        :param description: additional description allowing you to further document the field.
        """
        if entity is not None:
            if isinstance(entity, type):
                entity = entity.__name__
            desc = f"identifier uniquely representing a {entity} within the system. {description}"
        else:
            desc = f"Unique identifier representing the involved entity. {description}"
        return graphene.ID(required=True, description=desc)

    @classmethod
    def required_list_of_nonnull_elements(cls, entity: Union[type, str, Callable[[], type]], description: str = None):
        """
        A django_toolbox object may have associated a list of elements. the list itself needs to be present
        and all elements inside that list needs not to be null

        :param entity: object to be fed into a graphene_toolbox.List. Either a type, a string representing a type
        or a supplier function yielding the type of cell the list contains. If it is a string, for federations
        it is required to specify the full module path (since reference may be present).
        :param description: An optional description that can be used to improve graphql_toolsbox query documentation
        """

        if isinstance(entity, type):
            desc = f"Required list of elements, each of type {entity.__name__}. {description}"
        elif hasattr(entity, "__call__"):
            desc = f"Required list of {entity}, each of them non null. {description}"
        elif isinstance(entity, str):
            desc = f"Required list of elements, each of type {entity}. {description}"
        return graphene.List(entity, required=True, description=desc)

    @classmethod
    def required_boolean(cls, description: str = None) -> graphene.Boolean:
        """
        A boolean, which needs to be specified
        """
        return graphene.Boolean(required=True, description=description)

    @classmethod
    def required_string(cls, description: str = None) -> graphene.String:
        """
        a reference of the value fo a field
        """
        return graphene.String(required=True, description=description)

    @classmethod
    def required_int(cls, description: str = None) -> graphene.Int:
        """
        an int that needs to be specified
        """
        return graphene.Int(required=True, description=description)

    @classmethod
    def required_arrow_datetime(cls, description: str = None) -> ArrowDateTimeScalar:
        return ArrowDateTimeScalar(required=True, description=description)

    @classmethod
    def required_arrow_date(cls, description: str = None) -> ArrowDateScalar:
        return ArrowDateScalar(required=True, description=description)

    @classmethod
    def required_arrow_duration(cls, description: str = None) -> ArrowDurationScalar:
        return ArrowDurationScalar(required=True, description=description)

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
    def argument_required_input_list(cls, input_type: type, description: str = None) -> graphene.Argument:
        """
        String list that can be used to represents some entities (e.g., codename of permissions). Used within Argument metaclass for mutations

        :param input_type: name of the class of the entity this id represents. The class needs to extend InputDjangoObjectType
        :param description: description of the argument. it will be concatenated with the generated information
        """
        if description is None:
            description = f"List of inputs"
        return graphene.Argument(graphene.List(input_type), required=True, description=description)

    @classmethod
    def argument_required_string_list(cls, entity: Union[type, str] = None,
                                      description: str = None) -> graphene.Argument:
        """
        String list that can be used to represents some entities (e.g., codename of permissions). Used within Argument metaclass for mutations

        :param entity: name of the class of the entity this id represents
        :param description: description of the argument. it will be concatenated with the generated information
        """
        if entity is not None:
            if isinstance(entity, type):
                entity = entity.__name__
            desc = f"srting identifiers each uniquely representing a {entity} within the system."
        else:
            desc = f"Unique identifier list each representing an entity."
        if description is not None:
            desc += description
        return graphene.Argument(graphene.List(graphene.String), required=True, description=desc)

    @classmethod
    def argument_required_string(cls, description: str = None) -> graphene.String:
        """
        a reference of the value fo a field. Used within Argument metaclass for mutations
        """
        return graphene.String(required=True, description=description)

    @classmethod
    def argument_nullable_string(cls, description: str = None) -> graphene.String:
        """
        Used within Argument metaclass for mutations.
        Tells you that the mutation requires to have a string argument which may be set to null

        :param description: description of the argument.
        """
        return graphene.String(required=False, description=description)

    @classmethod
    def argument_required_input(cls, input_type: type, description: str = None) -> graphene.Argument:
        """
        a reference of the value od a field. Used within Argument metaclass for mutations

        :param input_type: class extending DjangoInputObjectType
        :param description: if present, the help text to show to graphiQL
        :return: argument of a mutation
        """
        if description is None:
            if hasattr(input_type, "model"):
                description = f"input of type {input_type.model.__name__}"
            else:
                description = f"input type {input_type.__name__}"
        return graphene.Argument(input_type, required=True, description=description)

    @classmethod
    def argument_optional_input(cls, input_type: type, default_value: any, description: str = None) -> graphene.Argument:
        """
        a reference of the value of a field in graphql query/mutation parameter which is optional.
        Used within Argument metaclass for mutations.

        :param input_type: class extending DjangoInputObjectType
        :param default_value: if the value is not set by the user when calling the graphql server, we will use this default value
        :param description: if present, the help text to show to graphiQL
        :return: argument of a mutation
        .. ::sealso https://docs.graphene-python.org/en/latest/types/objecttypes/#graphql-argument-defaults
        """
        if description is None:
            if hasattr(input_type, "model"):
                m = input_type.model.__name__
            else:
                m = input_type.__name__
            description = f"""input of type {m}. The user can avoid writing it in the query. 
            If it happens, the default value is {default_value}"""
        return graphene.Argument(input_type, required=False, default_value=default_value, description=description)

    @classmethod
    def argument_nullable_input(cls, input_type: type, description: str = None) -> graphene.Argument:
        """
        a reference of the value of a field in graphql query/mutation parameter which is optional.
        If left missing, it has the implicit value of None
        Used within Argument metaclass for mutations.

        :param input_type: class extending DjangoInputObjectType
        :param description: if present, the help text to show to graphiQL
        :return: argument of a mutation
        .. ::sealso https://docs.graphene-python.org/en/latest/types/objecttypes/#graphql-argument-defaults
        """
        return cls.argument_optional_input(input_type, None, description)

    @classmethod
    def argument_jwt_token(cls) -> graphene.String:
        return graphene.String(
            required=False,
            description="jwt token used to authorize the request. If left out, we will use the token present in the Authroization header"
        )

    @classmethod
    def argument_required_arrow_datetime(cls, description: str = None) -> ArrowDateTimeScalar:
        return ArrowDateTimeScalar(required=True, description=description)

    @classmethod
    def argument_required_arrow_date(cls, description: str = None) -> ArrowDateScalar:
        return ArrowDateScalar(required=True, description=description)

    @classmethod
    def argument_required_arrow_duration(cls, description: str = None) -> ArrowDurationScalar:
        return ArrowDurationScalar(required=True, description=description)

    # RETURN VALUES

    @classmethod
    def returns_id_list(cls, entity_type: Union[type, str], description: str = None) -> graphene.List:
        """
        A boolean, which tells if the mutation was successful or not

        :param entity_type: class extending models.Model
        :param description: description of the list
        :return: graphene_toolbox type
        """
        if isinstance(entity_type, str):
            entity_name = entity_type
        elif isinstance(entity_type, type):
            entity_name = entity_type.__name__
        else:
            raise TypeError(f"invalid type {entity_type}!")
        return graphene.List(graphene.ID, required=True,
                             description=f"{MUTATION_FIELD_DESCRIPTION}. List of {entity_name} ids. {description}")

    @classmethod
    def return_ok(cls, description: str = None) -> graphene.Boolean:
        """
        A boolean, which tells if the mutation was successful or not, as the return value of either a query or a grpahql mutation

        :param description: additional description for the query. It will be concatenated after the default description
        :return: graphene_toolbox type
        """
        return graphene.Boolean(required=True,
                                description=f"{MUTATION_FIELD_DESCRIPTION} True if the oepration was successful, false otherwise")

    @classmethod
    def returns_nonnull_id(cls, description: str = None) -> graphene.ID:
        """
        A int, which needs to be always present, as the return value of either a query or a grpahql mutation

        :param description: additional description for the query. It will be concatenated after the default description
        :return: graphene_toolbox type
        """
        return graphene.ID(required=True, description=f"{MUTATION_FIELD_DESCRIPTION} {description or ''}")

    @classmethod
    def returns_nonnull_boolean(cls, description: str = None) -> graphene.Boolean:
        """
        A boolean, which needs to be always present, as the return value of either a query or a grpahql mutation

        :param description: additional description for the query. It will be concatenated after the default description
        :return: graphene_toolbox type
        """
        return graphene.Boolean(required=True, description=f"{MUTATION_FIELD_DESCRIPTION} {description or ''}")

    @classmethod
    def returns_nonnull_int(cls, description: str = None) -> graphene.Int:
        """
        A int, which needs to be always present, as the return value of either a query or a grpahql mutation

        :param description: additional description for the query. It will be concatenated after the default description
        :return: graphene_toolbox type
        """
        return graphene.Int(required=True, description=f"{MUTATION_FIELD_DESCRIPTION} {description or ''}")

    @classmethod
    def returns_nonnull_float(cls, description: str = None) -> graphene.Float:
        """
        A float, which needs to be always present, as the return value of either a query or a grpahql mutation

        :param description: additional description for the query. It will be concatenated after the default description
        :return: graphene_toolbox type
        """
        return graphene.Float(required=True, description=f"{MUTATION_FIELD_DESCRIPTION} {description or ''}")

    @classmethod
    def returns_nonnull_string(cls, description: str = None) -> graphene.String:
        """
        A strnig, which needs to be always present, as the return value of either a query or a grpahql mutation

        :param description: additional description for the query. It will be concatenated after the default description
        :return: graphene_toolbox type
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
    def return_nullable(cls, return_type: type, description: str = None) -> graphene.Field:
        """
        tells the system that the mutation returns a value whcih may also be null

        :param return_type: class extending DjangoObjectType.
        :param description: if present, the help text to show to graphiQL
        :return: return value of a mutation
        """
        if description is None:
            description = ""
        return graphene.Field(return_type, description=f"{MUTATION_FIELD_DESCRIPTION} {description}", required=False)

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
        return graphene.Field(graphene.List(return_type), description=f"{MUTATION_FIELD_DESCRIPTION} {description}",
                              required=True)

    @classmethod
    def returns_nonnull_idlist(cls, concept: str = None, description: str = None) -> graphene.Field:
        """
        tells the system that the mutation returns a lnon null list of ids

        :param concept: cocnept a generic id in the list represents
        :param description: if present, the help text to show to graphiQL
        :return: return value of a mutation
        """
        if description is None:
            description = f"List of ID, each representing a single {concept}"
        return graphene.Field(graphene.List(graphene.ID(required=True)), description=f"{MUTATION_FIELD_DESCRIPTION} {description}",
                              required=True)
