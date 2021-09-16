import ast
import datetime
import functools
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

from django_koldar_utils.django import django_helpers
from rest_framework import serializers

from django_koldar_utils.graphql.graphql_types import TGrapheneReturnType, TGrapheneQuery, TGrapheneMutation, \
    TGrapheneInputType, TGrapheneType
from django_koldar_utils.graphql.scalars.ArrowDateScalar import ArrowDateScalar
from django_koldar_utils.graphql.scalars.ArrowDateTimeScalar import ArrowDateTimeScalar
from django_koldar_utils.graphql.scalars.ArrowDurationScalar import ArrowDurationScalar


def convert_field_into_input(field_specifier: Union[str, graphene.Field, models.Field], graphene_field: TGrapheneReturnType = None, graphene_type: Union[TGrapheneQuery, TGrapheneMutation] = None) -> TGrapheneReturnType:
    """
    Convert a graphene type (or a field from the django model) into an input one.

    :param graphene_field: if set, we will convert a graphene type into an input type (e.g. Field(Float) into float)
    :param graphene_type: if graphene_field is None, we convert the association graphene field belonging to the django model model_field
        (e.g., BigInteger into ID)
    :param field_specifier: if graphene_field is None, we need something tha tspecify what it the field in graphene_type
        that we want to convert. May be:
         - the field name in the graphene type to convert;
         - the graphene field instance;
         - the django model field instance (we assume there is the same name);
    """
    if graphene_field is not None:
        t = graphene_field
    elif graphene_type is not None:
        if isinstance(field_specifier, UnmountedType):
            t = graphene_type._meta.fields[field_specifier.attname]
        if isinstance(field_specifier, models.Field):
            t = graphene_type._meta.fields[field_specifier.attname]
        elif isinstance(field_specifier, str):
            t = graphene_type._meta.fields[field_specifier]
        else:
            raise TypeError(f"invalid type {field_specifier}!")
    else:
        raise ValueError(f"either graphene_field or graphene_type needs to be set")

    # if the type is a Field, fetch encapsuled type
    if isinstance(t, graphene.Field):
        # a field may have "of_type" or "_type" inside it  conaining the actual field to convert
        if hasattr(t.type, "of_type"):
            graphene_field_type = t.type.of_type
        else:
            # this represents a complex graphql object (e.g. AuthorGraphQL). We need to convert it into an input
            raise NotImplementedError()
    else:
        graphene_field_type = t.type


    # we need to fetch the corresponding field and strap away the possible "required" field. The rest can remain the same
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
    elif graphene_field_type._meta.name == "ArrowDateTimeScalar":
        v = ArrowDateTimeScalar(required=False, default_value=t.default_value, description=t.description, **t.args)
    elif graphene_field_type._meta.name == "ArrowDateScalar":
        v = ArrowDateScalar(required=False, default_value=t.default_value, description=t.description, **t.args)
    elif graphene_field_type._meta.name == "ArrowDurationScalar":
        v = ArrowDurationScalar(required=False, default_value=t.default_value, description=t.description, **t.args)
    elif graphene_field_type._meta.name == "Base64":
        v = graphene.Base64(required=False, default_value=t.default_value, description=t.description, **t.args)
    elif graphene_field_type._meta.name == "Float":
        v = graphene.Float(required=False, default_value=t.default_value, description=t.description, **t.args)
    else:
        raise ValueError(f"cannot handle type {t} (name = {graphene_field_type._meta.name})!")

    return v


# ##########################################################
# GRAPHENE CLASS
# ##########################################################


def create_graphene_tuple_input_type(name: str, it: Iterable[Tuple[str, TGrapheneInputType]]) -> TGrapheneInputType:
    """
    Programmatically create a type in graphene repersenting a tuple of elements.

    :param name: name of the type
    :param it: an iteralbe of pairs, where the frist item is the field name repersenting the i-th element
        while the second item is the graphene.FIeld type of said graphene class field
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
    Programmatically create a type in graphene repersenting a tuple of elements.

    :param name: name of the type
    :param description: optional description of this tuple
    :param it: an iteralbe of pairs, where the frist item is the field name repersenting the i-th element
        while the second item is the graphene.FIeld type of said graphene class field
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
    Programmatically create a type in graphene repersenting a pair of elements.

    :param name: name of the type
    :param item0_name: field name of the first item
    :param item0_type: field graphene.FIeld type of the first item
    :param item1_name: field name of the second item
    :param item1_type: field graphene.FIeld type of the second item
    :return: type rerpesenting the tuple
    """
    return create_graphene_tuple_type(name, [(item0_name, item0_type), (item1_name, item1_type)])


def create_graphql_class(cls, fields=None, specify_fields: Dict[str, Tuple[type, Optional[Callable[[any, any], any]]]]=None) -> type:
    """
    Create a graphQl type starting from a Django model

    :param cls: django type of the model whose graphql type we want to generate
    :param fields: field that we wna tto include in the graphene class type
    :param specify_fields: a dictionary of django model fields which you want to personally customize.
        Each dictionary key is a django model field name. Each value is a pair. If present, "fields" is ignored
         - first, mandatory, is the graphene type that you want to use for the field
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
    # attach graphql type additional fields
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

# ##########################################################
# GRAPHENE INPUT
# ##########################################################


def _create_graphql_input(graphene_type: TGrapheneType, class_name: str, fields: Iterable[any], generate_input_field: Callable[[str, any, TGrapheneType], TGrapheneType], description: str = None, get_field_name: Callable[[any], str] = None, get_associated_django_model: Callable[[TGrapheneReturnType], str] = None, should_be_excluded: Callable[[str, any], bool] = None) -> type:
    """
    Create an input class from a **django model** specifying only primitive types.
    All such types are optional (not required)

    :param graphene_type: graphene type that we will use to create the assoicated graphene input type
    :param class_name: name of the input class to create
    :param fields: fields of the graphene type (or maybe the associated django type) that we will use to crfeate the input
    :param generate_input_field: a callable that generates a graphene input type associated with a particular field
    :param description: descritpion of the input class. None to put a defualt one
    :param get_field_name: callable used to fetch the field name from an element of the field iterable
    :param get_associated_django_model: callable used to fetch the associated django model from the graphene type.
        If returns none, we will no include the "model" field in the meta input class
    :param should_be_excluded: a callable that check if the field should be excluded or not
    :return: input class
    """

    # class PersonInput(graphene.InputObjectType):
    #     name = graphene.String(required=True)
    #     age = graphene.Int(required=True)

    def default_get_field_name(f) -> str:
        return f.attname

    def default_get_associated_django_model(t: TGrapheneReturnType) -> Optional[models.Model]:
        return None

    def default_should_be_excluded(name: str, f: any) -> bool:
        return False

    if description is None:
        description = f"""The graphql input type associated to the type {class_name}. See {class_name} for further information"""
    if get_field_name is None:
        get_field_name = default_get_field_name
    if get_associated_django_model is None:
        get_associated_django_model = default_get_associated_django_model
    if should_be_excluded is None:
        should_be_excluded = default_should_be_excluded

    primitive_fields = {}
    for field in fields:
        field_name = get_field_name(field)
        if should_be_excluded(field_name, field):
            continue

        v = generate_input_field(field_name, field, graphene_type)
        primitive_fields[field_name] = v

    associated_django_type = get_associated_django_model(graphene_type)
    properties = {}
    properties["description"] = description
    properties["__doc__"] = description
    if associated_django_type is not None:
        properties["model"] = associated_django_type
    properties.update(primitive_fields)

    input_graphql_type = type(
        class_name,
        (graphene.InputObjectType, ),
        properties
    )

    return input_graphql_type





def create_graphql_primitive_input(django_type: type, graphene_type: type, exclude_fields: List[str] = None) -> type:
    """
    Create an input class from a **django model** specifying only primitive types.
    All such types are optional (not required)
    """

    if exclude_fields is None:
        exclude_fields = []

    def generate_input_field(field_name: str, f: any, graphene_type: TGrapheneType) -> any:
        v = convert_field_into_input(
            graphene_type=graphene_type,
            field_specifier=f,
        )
        return v

    def should_be_exluded(field_name: str, f: any) -> bool:
        nonlocal exclude_fields
        return field_name in exclude_fields

    class_name = django_type.__name__
    result = _create_graphql_input(
        class_name=f"{stringcase.pascalcase(class_name)}PrimitiveGraphQLInput",
        graphene_type=graphene_type,
        fields=django_helpers.get_primitive_fields(django_type),
        description=f"""The graphql input tyep associated to the type {class_name}. See {class_name} for further information""",
        generate_input_field=generate_input_field,
        should_be_excluded=should_be_exluded,
    )

    return result


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


def create_graphene_tuple_input(name: str, it: Iterable[Tuple[str, TGrapheneInputType]], description: str = None) -> TGrapheneInputType:
    """
    Programmatically create a type in graphene repersenting an input tuple of elements.

    :param name: name of the type
    :param description: optional description of this tuple
    :param it: an iteralbe of pairs, where the frist item is the field name repersenting the i-th element
        while the second item is the graphene.FIeld type of said graphene class field
    :return: graphene input type rerpesenting the tuple
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