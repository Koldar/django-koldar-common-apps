import abc
import ast
import datetime
import functools
import tarfile
from collections import OrderedDict
from typing import Iterable, Tuple, List, Union, Dict, Callable, Optional

import django.db.models
from django.db import models

import arrow
import graphene
import django_filters
import stringcase
from arrow import Arrow
from graphene import Scalar, Field
from graphene.types.unmountedtype import UnmountedType
from graphql.language import ast
from graphene_django import DjangoObjectType
from graphene_django_extras import LimitOffsetGraphqlPagination, DjangoInputObjectType, DjangoListObjectType

from django_koldar_utils.django_toolbox import django_helpers
from rest_framework import serializers

from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.GrapheneRegister import GrapheneRegister
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneReturnType, TGrapheneQuery, TGrapheneMutation, \
    TGrapheneInputType, TGrapheneType, TDjangoModelType
from django_koldar_utils.graphql_toolsbox.input_generators import AbstractGrapheneInputGenerator, \
    PrimitiveInputGenerator, StandardInputGenerator
from django_koldar_utils.graphql_toolsbox.scalars.ArrowDateScalar import ArrowDateScalar
from django_koldar_utils.graphql_toolsbox.scalars.ArrowDateTimeScalar import ArrowDateTimeScalar
from django_koldar_utils.graphql_toolsbox.scalars.ArrowDurationScalar import ArrowDurationScalar





# ##########################################################
# GRAPHENE CLASS
# ##########################################################


def create_graphene_tuple_input_type(name: str, it: Iterable[Tuple[str, TGrapheneInputType]]) -> TGrapheneInputType:
    """
    Programmatically create a type in graphene_toolbox repersenting a tuple of elements.

    :param name: name of the type
    :param it: an iteralbe of pairs, where the frist item is the field name repersenting the i-th element
        while the second item is the graphene_toolbox.FIeld type of said graphene_toolbox class field
    :return: type rerpesenting the tuple
    """
    properties = dict()
    for key, type in it:
        properties[key] = convert_field_into_input(graphene_field=type)
    result = type(
        name,
        (graphene.InputObjectType, ),
        properties
    )
    return result


def create_graphene_tuple_type(name: str, it: Iterable[Tuple[str, type]], description: str = None) -> type:
    """
    Programmatically create a type in graphene_toolbox repersenting a tuple of elements.

    :param name: name of the type
    :param description: optional description of this tuple
    :param it: an iteralbe of pairs, where the frist item is the field name repersenting the i-th element
        while the second item is the graphene_toolbox.FIeld type of said graphene_toolbox class field
    :return: type rerpesenting the tuple
    """
    l = list(it)

    if description is None:
        tuple_repr = '\n'.join(map(lambda pair: f" - {pair[0]} item is representing {pair[1][0]}", enumerate(l)))
        description = f"""Class that represents a tuple of size {len(l)} where: {tuple_repr}\n The tuple does not have further semantics."""

    properties = dict()
    for key, atype in l:
        if not isinstance(atype, graphene.Field):
            # fi the type is a scalar or a grapèhene type, we need to manually wrap it to Field.
            # in this way the type will appear in the _meta.fields as well
            atype = graphene.Field(atype)
        properties[key] = atype
    properties["__doc__"] = description

    result = type(
        name,
        (graphene.ObjectType, ),
        properties
    )
    return result


def create_graphene_pair_type(name: str, item0_name: str, item0_type: type, item1_name: str, item1_type: type) -> type:
    """
    Programmatically create a type in graphene_toolbox repersenting a pair of elements.

    :param name: name of the type
    :param item0_name: field name of the first item
    :param item0_type: field graphene_toolbox.FIeld type of the first item
    :param item1_name: field name of the second item
    :param item1_type: field graphene_toolbox.FIeld type of the second item
    :return: type rerpesenting the tuple
    """
    return create_graphene_tuple_type(name, [(item0_name, item0_type), (item1_name, item1_type)])


def create_graphql_class(cls, fields=None, specify_fields: Dict[str, Tuple[type, Optional[Callable[[any, any], any]]]]=None) -> type:
    """
    Create a graphQl type starting from a Django model

    :param cls: django_toolbox type of the model whose graphql_toolsbox type we want to generate
    :param fields: field that we wna tto include in the graphene_toolbox class type
    :param specify_fields: a dictionary of django_toolbox model fields which you want to personally customize.
        Each dictionary key is a django_toolbox model field name. Each value is a pair. If present, "fields" is ignored
         - first, mandatory, is the graphene_toolbox type that you want to use for the field
         - second, (optionally set to None) is a callable representing the resolver. If left missing we will just call
            the model field
    """

    def default_resolver(model_instance, info, field_name: str = None) -> any:
        return getattr(model_instance, field_name)

    if fields is None:
        fields = "__all__"
    if specify_fields is None:
        specify_fields = dict()

    meta_properties = {
        "model": cls,
        "description": cls.__doc__,
    }
    if len(specify_fields) > 0:
        meta_properties["exclude"] = list(specify_fields.keys())
    else:
        meta_properties["fields"] = fields
    graphql_type_meta = type(
        "Meta",
        (object, ),
        meta_properties
    )

    class_name = cls.__name__
    properties = {
        "Meta": graphql_type_meta,
    }
    # attach graphql_toolsbox type additional fields
    for field_name, value in specify_fields.items():
        if isinstance(value, tuple):
            graphene_type, resolver_function = value
        else:
            graphene_type = value
            resolver_function = None

        properties[field_name] = graphene_type
    for field_name, value in specify_fields.items():
        if isinstance(value, tuple):
            graphene_type, resolver_function = value
        else:
            graphene_type = value
            resolver_function = None

        if resolver_function is None:
            resolver_function = functools.partial(default_resolver, field_name=field_name)
        properties[f"resolve_{field_name}"] = resolver_function

    graphql_type = type(
        f"{class_name}GraphQLType",
        (DjangoObjectType, ),
        properties
    )

    return graphql_type


def create_graphql_list_type(cls) -> type:
    """
    A graphql_toolsbox type representing a list of a given class.
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

# ##########################################################
# GRAPHENE REGISTER
# ##########################################################

DEFAULT_REGISTER: GrapheneRegister = GrapheneRegister()
DEFAULT_REGISTER.register_base_types("default")
DEFAULT_GRAPHENE_INPUT_GENERATOR: AbstractGrapheneInputGenerator = StandardInputGenerator()
DEFAULT_GRAPHENE_PRIMITIVE_INPUT_GENERATOR: AbstractGrapheneInputGenerator = PrimitiveInputGenerator()


def create_graphql_primitive_input(django_type: type, graphene_type: type, exclude_fields: List[str] = None) -> type:
    """
    Create an input class from a **django_toolbox model** specifying only primitive types.
    All such types are optional (not required)
    """

    if exclude_fields is None:
        exclude_fields = []

    # def generate_input_field(field_name: str, f: any, graphene_type: TGrapheneType) -> any:
    #     v = convert_field_into_input(
    #         graphene_type=graphene_type,
    #         field_specifier=f,
    #     )
    #     return v
    #
    # def should_be_exluded(field_name: str, f: any) -> bool:
    #     nonlocal exclude_fields
    #     return field_name in exclude_fields

    class_name = django_type.__name__
    field_names = list(map(lambda x: x.name, filter(lambda x: x.name in exclude_fields, django_helpers.get_primitive_fields(django_type))))

    result = DEFAULT_GRAPHENE_PRIMITIVE_INPUT_GENERATOR.create_graphql_input_type(
        graphene_type=graphene_type,
        class_name=f"{stringcase.pascalcase(class_name)}PrimitiveGraphQLInput",
        field_names=field_names,
        description=f"""The graphql_toolsbox input tyep associated to the type {class_name}. See {class_name} for further information""",
        register=DEFAULT_REGISTER,
    )
    return result

    # class_name = django_type.__name__
    # result = _create_graphql_input(
    #     class_name=f"{stringcase.pascalcase(class_name)}PrimitiveGraphQLInput",
    #     graphene_type=graphene_type,
    #     fields=django_helpers.get_primitive_fields(django_type),
    #     description=f"""The graphql_toolsbox input tyep associated to the type {class_name}. See {class_name} for further information""",
    #     generate_input_field=generate_input_field,
    #     should_be_excluded=should_be_exluded,
    # )
    #
    # return result


def create_graphql_input(cls) -> type:
    """
    Create a graphene input by calling django extra package.
    Note that this will not include the id. You may need it or not.
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


def create_graphene_tuple_input(name: str, it: Iterable[Tuple[str, TGrapheneInputType]], description: str = None) -> TGrapheneInputType:
    """
    Programmatically create a type in graphene_toolbox repersenting an input tuple of elements.

    :param name: name of the type
    :param description: optional description of this tuple
    :param it: an iteralbe of pairs, where the frist item is the field name repersenting the i-th element
        while the second item is the graphene_toolbox.FIeld type of said graphene_toolbox class field
    :return: graphene_toolbox input type rerpesenting the tuple
    """
    l = list(it)

    if description is None:
        tuple_repr = '\n'.join(map(lambda pair: f" - {pair[0]} item is representing {pair[1][0]}", enumerate(l)))
        description = f"""Class that represents a tuple of size {len(l)} where: {tuple_repr}\n The tuple does not have further semantics."""

    properties = dict()
    for key, atype in l:
        if not isinstance(atype, graphene.Field):
            # fi the type is a scalar or a grapèhene type, we need to manually wrap it to Field.
            # in this way the type will appear in the _meta.fields as well
            # we mark the field as non required, since this is an input
            atype = graphene.Field(atype, required=False)
        properties[key] = atype
    properties["__doc__"] = description

    result = type(
        name,
        (graphene.InputObjectType, ),
        properties
    )
    return result


# ################################################################
# SERIALIZERS
# ################################################################



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