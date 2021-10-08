import abc
from typing import List, Iterable, Union

import graphene
import stringcase

from django_koldar_utils.django_toolbox import django_helpers
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper
from django_koldar_utils.graphql_toolsbox.GrapheneRegister import GrapheneRegister
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneReturnType, TGrapheneType


class AbstractGrapheneInputGenerator(abc.ABC):
    """
    An object that allows you to generate inputs starting from types
    """

    @abc.abstractmethod
    def _convert_field_into_input(self, field_name: str,
                                graphene_field: TGrapheneReturnType,
                                graphene_field_original: TGrapheneReturnType,
                                graphene_type: TGrapheneType,
                                register: GrapheneRegister,
                                  ) -> TGrapheneReturnType:
        """
        Convert a graphene type (or a field from the django_toolbox model) into a type that can be used in a input.

        :param register:  register to fetch input of complex object whose input
            is not straightforward to compute
        :param graphene_field: the field to convert. Thsi value has been preprocessed to specify only the important bit
            of the type
        :param graphene_field_original: the field to convert. Fetched from graphene_type
        :param graphene_type: if graphene_field is None, we convert the association graphene_toolbox field belonging to the django_toolbox model model_field
            (e.g., BigInteger into ID)
        :param field_specifier: if graphene_field is None, we need something tha tspecify what it the field in graphene_type
            that we want to convert. May be:
             - the field name in the graphene_toolbox type to convert;
             - the graphene_toolbox field instance;
             - the django_toolbox model field instance (we assume there is the same name);
        """
        pass

        # # query the register and fetch the association graphene input
        # graphene_input_type = register.get_main_graphene_input_type_from_graphene_type(graphene_field)
        # result = graphene_input_type(
        #     required=False,
        #     default_value=graphene_field_original.default_value,
        #     description=graphene_field_original.description,
        #     **graphene_field_original.args
        # )
        # return result

        # # if the type is a Field, fetch encapsuled type
        # if isinstance(t, graphene.Field):
        #     # a field may have "of_type" or "_type" inside it  conaining the actual field to convert
        #     if hasattr(t.type, "of_type"):
        #         graphene_field_type = t.type.of_type
        #     else:
        #         # this represents a complex graphql_toolsbox object (e.g. AuthorGraphQL). We need to convert it into an input
        #         raise NotImplementedError()
        # else:
        #     graphene_field_type = t.type
        #
        # # we need to fetch the corresponding field and strap away the possible "required" field. The rest can remain the same
        # if graphene_field_type._meta.name == "String":
        #     v = graphene.String(required=False, default_value=t.default_value, description=t.description, **t.args)
        # elif graphene_field_type._meta.name == "Int":
        #     v = graphene.Int(required=False, default_value=t.default_value, description=t.description, **t.args)
        # elif graphene_field_type._meta.name == "Boolean":
        #     v = graphene.Boolean(required=False, default_value=t.default_value, description=t.description, **t.args)
        # elif graphene_field_type._meta.name == "ID":
        #     v = graphene.ID(required=False, default_value=t.default_value, description=t.description, **t.args)
        # elif graphene_field_type._meta.name == "DateTime":
        #     v = graphene.DateTime(required=False, default_value=t.default_value, description=t.description, **t.args)
        # elif graphene_field_type._meta.name == "Date":
        #     v = graphene.Date(required=False, default_value=t.default_value, description=t.description, **t.args)
        # elif graphene_field_type._meta.name == "ArrowDateTimeScalar":
        #     v = ArrowDateTimeScalar(required=False, default_value=t.default_value, description=t.description, **t.args)
        # elif graphene_field_type._meta.name == "ArrowDateScalar":
        #     v = ArrowDateScalar(required=False, default_value=t.default_value, description=t.description, **t.args)
        # elif graphene_field_type._meta.name == "ArrowDurationScalar":
        #     v = ArrowDurationScalar(required=False, default_value=t.default_value, description=t.description, **t.args)
        # elif graphene_field_type._meta.name == "Base64":
        #     v = graphene.Base64(required=False, default_value=t.default_value, description=t.description, **t.args)
        # elif graphene_field_type._meta.name == "Float":
        #     v = graphene.Float(required=False, default_value=t.default_value, description=t.description, **t.args)
        # else:
        #     raise ValueError(f"cannot handle type {t} (name = {graphene_field_type._meta.name})!")
        #
        # return v

    @abc.abstractmethod
    def _should_you_include_field(self, field_name: str, field_type: TGrapheneReturnType, original_field_type: TGrapheneReturnType) -> bool:
        """
        Check if you should include the field in the input to generate

        :param field_name: name of the field to consider
        :param field_type: pre-processed type of field_name. If possible, use this: it is much easier to handle
        :param original_field_type: original type of the field_name
        :return: treu if this field should be considered, false otherwise
        """
        pass

    def _get_field(self, t: Union[TGrapheneType], name: str) -> TGrapheneReturnType:
        """
        :param t: the entity owning the field
        :param name: name of the field to fetch
        :raise KeyError: if we cannot find the field in the type
        :return: graphene type isntance representing the field
        """
        result = t._meta.fields[name]
        result = GraphQLHelper.get_actual_type_from_field(result)
        return result

    def create_graphql_input_type(self, graphene_type: TGrapheneType, class_name: str, field_names: Iterable[str],
                            description: str = None,
                            register: GrapheneRegister = None,
                              ) -> type:
        """
        Create an input class from a **django_toolbox model** specifying only primitive types.
        All such types are optional (not required)

        :param graphene_type: graphene type that we will use to create the assoicated graphene_toolbox input type
        :param class_name: name of the input class to create
        :param field_names: field names of the graphene_toolbox type (or maybe the associated django_toolbox type) that we will use to create the input
        :param description: descritpion of the input class. None to put a defualt one
            If returns none, we will no include the "model" field in the meta input class
        :param register: a structure that maps types and fetch their corresponding graphene and input types
        :return: input class
        """

        # class PersonInput(graphene.InputObjectType):
        #     name = graphene.String(required=True)
        #     age = graphene.Int(required=True)

        if description is None:
            description = f"""The graphene input type associated to the type {class_name}. See {class_name} for further information"""

        input_fields = {}
        for field_name in field_names:
            try:
                graphene_field_original = graphene_type._meta.fields[field_name]
                field = self._get_field(graphene_type, field_name)
            except AttributeError:
                # we could not find the field in the graphene type
                continue
            except KeyError:
                # we could not find the field
                continue
            if not self._should_you_include_field(field_name, field, graphene_field_original):
                continue
            v = self._convert_field_into_input(
                field_name=field_name,
                graphene_field_original=graphene_field_original,
                graphene_field=field,
                graphene_type=graphene_type,
                register=register,
            )
            input_fields[field_name] = v

        properties = dict()
        properties["description"] = description
        properties["__doc__"] = description
        properties.update(input_fields)

        input_graphql_type = type(
            class_name,
            (graphene.InputObjectType,),
            properties
        )

        return input_graphql_type

    # def generate_primitive_input(self, django_type: TDjangoModelType, graphene_type: TGrapheneType, exclude_fields: List[str] = None) -> TGrapheneInputType:
    #     """
    #     Create an input class from a **django model** specifying only primitive types.
    #     The fields of the django type will become all optional (not required)
    #     """
    #
    #     if exclude_fields is None:
    #         exclude_fields = []
    #
    #     def generate_input_field(field_name: str, f: any, graphene_type: TGrapheneType) -> any:
    #         v = self._convert_field_into_input(
    #             graphene_type=graphene_type,
    #             field_specifier=f,
    #         )
    #         return v
    #
    #     def should_be_exluded(field_name: str, f: any) -> bool:
    #         nonlocal exclude_fields
    #         return field_name in exclude_fields
    #
    #     class_name = django_type.__name__
    #     result = self._create_graphql_input(
    #         class_name=f"{stringcase.pascalcase(class_name)}PrimitiveGraphQLInput",
    #         graphene_type=graphene_type,
    #         fields=django_helpers.get_primitive_fields(django_type),
    #         description=f"""The graphql_toolsbox input tyep associated to the type {class_name}. See {class_name} for further information""",
    #         generate_input_field=generate_input_field,
    #         should_be_excluded=should_be_exluded,
    #     )
    #
    #     return result


class MakeAllFieldsAsOptionalMixIn:

    def _convert_field_into_input(self, field_name: str,
                                  graphene_field: TGrapheneReturnType,
                                  graphene_field_original: TGrapheneReturnType,
                                  graphene_type: TGrapheneType,
                                  register: GrapheneRegister,
                                  ) -> TGrapheneReturnType:
        # query the register and fetch the association graphene input
        graphene_input_type = register.get_main_graphene_input_type_from_graphene_type(graphene_field)
        result = graphene_input_type(
            required=False,
            default_value=graphene_field_original.default_value,
            description=graphene_field_original.description,
            **graphene_field_original.args
        )
        return result


class ExcludePrimaryKeyMixIn:
    """
    MixIn to add to a AbstractGrapheneInputGenerator implementation
    exclude any field that is a primary key (type ID)
    """

    def _should_you_include_field(self, field_name: str, field_type: TGrapheneReturnType, original_field_type: TGrapheneReturnType) -> bool:
        return GraphQLHelper.is_field_id(field_type)


class ExcludeNonPrimitiveFieldMixIn:
    """
        MixIn to add to a AbstractGrapheneInputGenerator implementation
        Include everything!
        """

    def _should_you_include_field(self, field_name: str, field_type: TGrapheneReturnType, original_field_type: TGrapheneReturnType) -> bool:
        return not GraphQLHelper.is_field_non_primitive(original_field_type)


class IncludeEveryFieldMixIn:
    """
    MixIn to add to a AbstractGrapheneInputGenerator implementation
    Include everything!
    """

    def _should_you_include_field(self, field_name: str, field_type: TGrapheneReturnType,
                                  original_field_type: TGrapheneReturnType) -> bool:
        return True


class ExcludeSecretsMixIn:
    """
    MixIn to add to a AbstractGrapheneInputGenerator implementation
    Exclude all password related fields
    """

    def _should_you_include_field(self, field_name: str, field_type: TGrapheneReturnType, original_field_type: TGrapheneReturnType) -> bool:
        for x in ["password", "psw", "secret", "forget_token"]:
            if x in field_name:
                return False
        return True


class ExcludeActiveMixIn:
    """
    MixIn to add to a AbstractGrapheneInputGenerator implementation
    Exclude all field containign "active" word
    """

    def _should_you_include_field(self, field_name: str, field_type: TGrapheneReturnType, original_field_type: TGrapheneReturnType) -> bool:
        for x in ["active", ]:
            if x in field_name:
                return False
        return True


class ExcludeActiveAndSecrets:
    def _should_you_include_field(self, field_name: str, field_type: TGrapheneReturnType, original_field_type: TGrapheneReturnType) -> bool:
        return all(map(lambda cls: cls._should_you_include_field(self, field_name, field_type, original_field_type), [ExcludeActiveMixIn, ExcludeSecretsMixIn, ]))


class ExcludeActiveNonPrimitiveAndSecrets:
    def _should_you_include_field(self, field_name: str, field_type: TGrapheneReturnType, original_field_type: TGrapheneReturnType) -> bool:
        return all(map(lambda cls: cls._should_you_include_field(self, field_name, field_type, original_field_type), [ExcludeActiveMixIn, ExcludeSecretsMixIn, ExcludeNonPrimitiveFieldMixIn]))


class StandardInputGenerator(MakeAllFieldsAsOptionalMixIn, ExcludeActiveAndSecrets, AbstractGrapheneInputGenerator):
    """
    Inputs containing all fields in the graphene type, except active and sensitive ones. All fields are marked as optional
    """
    pass


class PrimitiveInputGenerator(MakeAllFieldsAsOptionalMixIn, ExcludeActiveNonPrimitiveAndSecrets, AbstractGrapheneInputGenerator):
    """
    Input containign only primitive fields, except active and sensitive ones. All fields are marked as optional
    """
    pass


