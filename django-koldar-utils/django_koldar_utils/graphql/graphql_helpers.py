from typing import Iterable, Tuple

import django_filters
from graphene_django import DjangoObjectType
from graphene_django_extras import LimitOffsetGraphqlPagination, DjangoInputObjectType, DjangoListObjectType
from rest_framework import serializers


def create_graphql_class(cls, fields = None) -> type:
    """
    Create a graphQl type starting from a Django model
    """
    if fields is None:
        fields = "__all__"
    graphql_type_meta = type(
        "Meta",
        (object, ),
        {
            "model": cls,
            "description": cls.__doc__,
            "fields": fields
        }
    )

    class_name = cls.__name__
    graphql_type = type(
        f"{class_name}GraphQLType",
        (DjangoObjectType, ),
        {
            "Meta": graphql_type_meta
        }
    )

    return graphql_type


def create_graphql_input(cls) -> type:
    """
    Create an input class from a django model.
    See https://github.com/eamigo86/graphene-django-extras
    """
    graphql_type_meta = type(
        "Meta",
        (object, ),
        {
            "model": cls,
            "description": f"""
                Input type of class {cls.__name__}.
            """
        }
    )

    class_name = cls.__name__
    graphql_type = type(
        f"{class_name}GraphQLInput",
        (DjangoInputObjectType, ),
        {
            "Meta": graphql_type_meta
        }
    )

    return graphql_type


def create_graphql_list_type(cls) -> type:
    """
    A graphql type representing a list of a given class.
    This is used to generate list of DjancoObjectType
    See https://github.com/eamigo86/graphene-django-extras
    """
    graphql_type_meta = type(
        "Meta",
        (object, ),
        {
            "model": cls,
            "description": f"""GraphQL type representing a list of {cls.__name__}.""",
            "pagination": LimitOffsetGraphqlPagination(default_limit=25)
        }
    )

    class_name = cls.__name__
    graphql_type = type(
        f"{class_name}GraphQLListType",
        (DjangoListObjectType, ),
        {
            "Meta": graphql_type_meta
        }
    )
    return graphql_type


#todo remove
# def create_graphql_input_list_type(model_type: type, input_type: type) -> type:
#     """
#     A graphql type representing a list of a given class.
#     This is used to generate list of DjangoInputObject. useful in mutations
#     See https://github.com/eamigo86/graphene-django-extras
#
#     :param model_type: django type
#     :param input_type: input type assopciatedto the django model
#     :return: class representing a list fo input types
#     """
#     graphql_type_meta = type(
#         "Meta",
#         (object, ),
#         {
#             "model": input_type,
#             "description": f"""GraphQL type representing a list of input of type {model_type.__name__}.""",
#             "pagination": LimitOffsetGraphqlPagination(default_limit=25)
#         }
#     )
#
#     graphql_type = type(
#         f"{model_type.__name__}GraphQLInputListType",
#         (DjangoListObjectType, ),
#         {
#             "Meta": graphql_type_meta
#         }
#     )
#     return graphql_type


def create_serializer(cls) -> type:
    """
    A serializer allowing to easily create mutations
    See https://github.com/eamigo86/graphene-django-extras
    """
    graphql_type_meta = type(
        "Meta",
        (object, ),
        {
            "model": cls,
        }
    )

    class_name = cls.__name__
    graphql_type = type(
        f"{class_name}Serializer",
        (serializers.ModelSerializer, ),
        {
            "Meta": graphql_type_meta
        }
    )
    return graphql_type