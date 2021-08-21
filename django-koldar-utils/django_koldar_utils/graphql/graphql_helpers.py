from typing import Iterable, Tuple, List

import graphene
import django_filters
import stringcase
from graphene_django import DjangoObjectType
from graphene_django_extras import LimitOffsetGraphqlPagination, DjangoInputObjectType, DjangoListObjectType
from django_koldar_utils.django import django_helpers
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


def create_graphql_primitive_input(django_type: type, graphene_type: type, exclude_fields: List[str] = None) -> type:
    """
    Create an input class from a django model specifying only primitive types.
    All such types are optional (not required)
    """

    # class PersonInput(graphene.InputObjectType):
    #     name = graphene.String(required=True)
    #     age = graphene.Int(required=True)

    if exclude_fields is None:
        exclude_fields = []

    class_name = django_type.__name__
    description = f"""The graphql input tyep associated to the type {class_name}. See {class_name} for further information"""

    primitive_fields = {}
    for field in django_helpers.get_primitive_fields(django_type):
        if field.attname in exclude_fields:
            continue
        t = graphene_type._meta.fields[field.attname]
        if isinstance(t, graphene.Field):
            graphene_field_type = t.type.of_type
        else:
            graphene_field_type = t.type

        if graphene_field_type._meta.name == "String":
            v = graphene.String(required=False, default_value=t.default_value, description=t.description, **t.args)
        elif graphene_field_type._meta.name == "Int":
            v = graphene.Int(required=False, default_value=t.default_value, description=t.description, **t.args)
        elif graphene_field_type._meta.name == "Boolean":
            v = graphene.Boolean(required=False, default_value=t.default_value, description=t.description, **t.args)
        elif graphene_field_type._meta.name == "ID":
            v = graphene.ID(required=False, default_value=t.default_value, description=t.description, **t.args)
        elif graphene_field_type._meta.name == "DateTime":
            v = graphene.DateTime(required=False, default_value=t.default_value, description=t.description, **t.args)
        elif graphene_field_type._meta.name == "Date":
            v = graphene.Date(required=False, default_value=t.default_value, description=t.description, **t.args)
        elif graphene_field_type._meta.name == "Base64":
            v = graphene.Base64(required=False, default_value=t.default_value, description=t.description, **t.args)
        elif graphene_field_type._meta.name == "Float":
            v = graphene.Float(required=False, default_value=t.default_value, description=t.description, **t.args)
        else:
            raise ValueError(f"cannot handle type {t}!")

        primitive_fields[field.attname] = v

    input_graphql_type = type(
        f"{stringcase.pascalcase(class_name)}PrimitiveGraphQLInput",
        (graphene.InputObjectType, ),
        {
            "model": django_type,
            "description": description,
            "__doc__": description,
            **primitive_fields
        }
    )

    return input_graphql_type


def create_graphql_input(cls) -> type:
    """
    See dujango extras
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