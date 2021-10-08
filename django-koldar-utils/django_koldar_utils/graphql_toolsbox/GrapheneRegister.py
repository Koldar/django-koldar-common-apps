import datetime
from collections import OrderedDict
from typing import Union, Dict, Optional, Iterable

import graphene
import stringcase
from arrow import arrow

from django_koldar_utils.graphql_toolsbox.scalars.ArrowDateTimeScalar import ArrowDateTimeScalar
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneReturnType, TGrapheneInputType, TGrapheneType
from django_koldar_utils.graphql_toolsbox.scalars.ArrowDateScalar import ArrowDateScalar
from django_koldar_utils.graphql_toolsbox.scalars.ArrowDurationScalar import ArrowDurationScalar


class GrapheneRegisterSlot(object):
    """
    A slot inside the register
    """

    __slots__ = ("atype", "graphene_type", "graphene_input_type", "django_field_type")

    def __init__(self, atype: type, graphene_type: TGrapheneReturnType, graphene_input_type: TGrapheneInputType,
                 django_field_type: type):
        self.atype = atype
        self.graphene_type = graphene_type
        self.graphene_input_type = graphene_input_type
        self.django_field_type = django_field_type

    def _get_non_none(self, x, y, both_none) -> any:
        if x is None and y is not None:
            return y
        elif x is not None and y is None:
            return x
        elif x is None and y is None:
            return both_none
        elif x is not None and y is not None and y == x:
            return x
        else:
            raise ValueError(f"Different values {x} and {y} mismatch for slot {self}!")

    def merge(self, other: "GrapheneRegisterSlot") -> "GrapheneRegisterSlot":
        result = GrapheneRegisterSlot(self.atype, self.graphene_type, self.graphene_input_type, self.django_field_type)
        result.atype = self._get_non_none(self.atype, other.atype, None)
        result.graphene_type = self._get_non_none(self.graphene_type, other.graphene_type, None)
        result.graphene_input_type = self._get_non_none(self.graphene_input_type, other.graphene_input_type, None)
        result.django_field_type = self._get_non_none(self.django_field_type, other.django_field_type, None)

        return result


class GrapheneRegister(object):
    """
    An object that allows you to fetch all the graphene a nd graphene input types for a specific
    type. The type does not need to be a django model. Can be anything.
    """

    def __init__(self):
        self._registry_find_by_type: Dict[type, OrderedDict[any, GrapheneRegisterSlot]] = dict()
        """
        key are types. the values is dictioanry indexed by label value. The inner dictionary is an OrderedDict
        becuase we assume that the first label registered is the most important (or default one)

        We trade memory to improve the query timinfg when fetching graphene types and inputs types for a specific type  
        """
        self._registry_by_graphene_type: Dict[TGrapheneType, OrderedDict[any, GrapheneRegisterSlot]] = dict()
        """
        key are graphene types. the values are dictionaries indexed by label value. The inner dictionary is 
        an OrderedDict
        becuase we assume that the first label registered is the most important (or default one)

        We trade memory to improve the query timing when fetching types and inputs types for a specific graphene type  
        """
        self._registry_by_graphene_input: Dict[type, OrderedDict[any, GrapheneRegisterSlot]] = dict()
        """
        key are graphene input types. the values are dictionaries indexed by label value. The inner dictionary is an 
        OrderedDict
        becuase we assume that the first label registered is the most important (or default one)

        We trade memory to improve the query timing when fetching types and inputs types for a specific graphene 
        input type  
        """

    def register_base_types(self, label: str):
        """
        Automatically adds some graphene types and inputs for some base scenarios

        :param label: label to assign o every type
        """

        # TODO djang_field is not used at the moment
        label = stringcase.snakecase(label)

        # primitive
        self.register_mapping(
            atype=str,
            graphene_type=graphene.String,
            graphene_input_type=graphene.String,
            django_field=str,
            label_from_type=label, label_from_graphene=label, label_from_graphene_input=label,
        )
        self.register_mapping(
            atype=int,
            graphene_type=graphene.Int,
            graphene_input_type=graphene.Int,
            django_field=int,
            label_from_type=label, label_from_graphene=label, label_from_graphene_input=label,
        )
        self.register_mapping(
            atype=float,
            graphene_type=graphene.Float,
            graphene_input_type=graphene.Float,
            django_field=float,
            label_from_type=label, label_from_graphene=label, label_from_graphene_input=label,
        )
        self.register_mapping(
            atype=bool,
            graphene_type=graphene.Boolean,
            graphene_input_type=graphene.Boolean,
            django_field=bool,
            label_from_type=label, label_from_graphene=label, label_from_graphene_input=label,
        )

        # id
        self.register_mapping(
            atype=int,
            graphene_type=graphene.ID,
            graphene_input_type=graphene.ID,
            django_field=int,
            label_from_type=f"{label}_id",
            label_from_graphene=f"{label}_id",
            label_from_graphene_input=f"{label}_id",
        )

        # datetimes
        self.register_mapping(
            atype=arrow.Arrow,
            graphene_type=graphene.DateTime,
            graphene_input_type=ArrowDateTimeScalar,
            django_field=int,
            label_from_type=f"{label}_arrow_datetime",
            label_from_graphene=f"{label}_arrow_datetime",
            label_from_graphene_input=f"{label}_arrow_datetime",
        )
        self.register_mapping(
            atype=datetime.datetime,
            graphene_type=graphene.DateTime,
            graphene_input_type=graphene.DateTime,
            django_field=int,
            label_from_type=f"{label}_legacy",
            label_from_graphene=f"{label}_legacy",
            label_from_graphene_input=f"{label}_legacy",
        )

        # dates
        self.register_mapping(
            atype=datetime.date,
            graphene_type=graphene.Date,
            graphene_input_type=graphene.Date,
            django_field=int,
            label_from_type=f"{label}_legacy",
            label_from_graphene=f"{label}_legacy",
            label_from_graphene_input=f"{label}_legacy",
        )
        self.register_mapping(
            atype=arrow.Arrow,
            graphene_type=graphene.Date,
            graphene_input_type=ArrowDateScalar,
            django_field=int,
            label_from_type=f"{label}_arrow_date",
            label_from_graphene=f"{label}_arrow_date",
            label_from_graphene_input=f"{label}_arrow_date",
        )

        # durations
        self.register_mapping(
            atype=datetime.timedelta,
            graphene_type=graphene.Int,
            graphene_input_type=ArrowDurationScalar,
            django_field=int,
            label_from_type=f"{label}_arrow_duration",
            label_from_graphene=f"{label}_arrow_duration",
            label_from_graphene_input=f"{label}_arrow_duration",
        )

        # base64
        self.register_mapping(
            atype=str,
            graphene_type=graphene.Base64,
            graphene_input_type=graphene.Base64,
            django_field=int,
            label_from_type=f"{label}_base64",
            label_from_graphene=f"{label}_base64",
            label_from_graphene_input=f"{label}_base64",
        )

        # duration

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

    def register_mapping(self, atype: type, graphene_type: TGrapheneType, graphene_input_type: TGrapheneInputType,
                         django_field: type, label_from_type: any, label_from_graphene: any,
                         label_from_graphene_input: any):
        self._add_representation(t=atype,
                                 graphene_type=graphene_type,
                                 graphene_input=graphene_input_type,
                                 django_field=django_field,
                                 label_from_type=label_from_type,
                                 label_from_graphene=label_from_graphene,
                                 label_from_graphene_input=label_from_graphene_input,
                                 )

    def _add_representation(self, t: type, graphene_type: TGrapheneType, graphene_input: Optional[TGrapheneInputType],
                            django_field: type, label_from_type: any, label_from_graphene: any,
                            label_from_graphene_input: any):
        new_slot = GrapheneRegisterSlot(atype=t, graphene_type=graphene_type, graphene_input_type=graphene_input,
                                        django_field_type=django_field)
        # _registry_find_by_type
        if t not in self._registry_find_by_type:
            self._registry_find_by_type[t] = OrderedDict()
        if label_from_type in self._registry_find_by_type[t]:
            # we try to merge
            present = self._registry_find_by_type[t][label_from_type]
            copy_slot = present.merge(new_slot)
        else:
            copy_slot = new_slot
        self._registry_find_by_type[t][label_from_type] = copy_slot

        # _registry_by_graphene_type
        if graphene_type not in self._registry_by_graphene_type:
            self._registry_by_graphene_type[graphene_type] = OrderedDict()
        if label_from_graphene in self._registry_by_graphene_type[graphene_type]:
            present = self._registry_by_graphene_type[graphene_type][label_from_graphene]
            copy_slot = present.merge(new_slot)
        else:
            copy_slot = new_slot
        self._registry_by_graphene_type[graphene_type][label_from_graphene] = copy_slot

        # _registry_by_graphene_input
        if graphene_input not in self._registry_by_graphene_input:
            self._registry_by_graphene_input[graphene_input] = OrderedDict()
        if label_from_graphene_input in self._registry_by_graphene_input[graphene_input]:
            present = self._registry_by_graphene_input[graphene_input][label_from_graphene_input]
            copy_slot = present.merge(new_slot)
        else:
            copy_slot = new_slot
        self._registry_by_graphene_input[graphene_input][label_from_graphene_input] = copy_slot

    def list_available_labels_for(self, atype: Union[type, TGrapheneType, TGrapheneInputType], target: str) -> Iterable[
        any]:
        if target == "type":
            yield from self._registry_find_by_type[atype].keys()
        elif target == "graphene":
            yield from self._registry_by_graphene_type[atype].keys()
        elif target == "input":
            yield from self._registry_by_graphene_input[atype].keys()
        else:
            raise ValueError(f"invalid target {target}")

    def list_available_labels_for_type(self, atype: type) -> Iterable[any]:
        return self.list_available_labels_for(atype, "type")

    def list_available_labels_for_graphene_type(self, atype: type) -> Iterable[any]:
        return self.list_available_labels_for(atype, "graphene")

    def list_available_labels_for_graphene_input_type(self, atype: type) -> Iterable[any]:
        return self.list_available_labels_for(atype, "input")

    def get_main_graphene_type_from_type(self, atype: type) -> TGrapheneType:
        return self._get_from(atype, generate="graphene", from_source="type")

    def get_main_graphene_input_type_from_type(self, atype: type, label: str = None) -> TGrapheneType:
        return self._get_from(atype, generate="input", from_source="type")

    def get_main_type_from_graphene_type(self, atype: TGrapheneType) -> TGrapheneType:
        return self._get_from(atype, generate="type", from_source="graphene")

    def get_main_graphene_input_type_from_graphene_type(self, atype: TGrapheneType) -> TGrapheneType:
        return self._get_from(atype, generate="input", from_source="graphene")

    def get_main_type_from_graphene_input_type(self, atype: TGrapheneType) -> TGrapheneType:
        return self._get_from(atype, generate="type", from_source="input")

    def get_main_graphene_type_from_graphene_input_type(self, atype: TGrapheneType) -> TGrapheneType:
        return self._get_from(atype, generate="graphene", from_source="input")

    def get_graphene_type_from_type(self, atype: type, label: str) -> TGrapheneType:
        return self._get_from(atype, generate="graphene", from_source="type", label=label)

    def get_graphene_input_type_from_type(self, atype: type, label: str) -> TGrapheneType:
        return self._get_from(atype, generate="input", from_source="type", label=label)

    def get_type_from_graphene_type(self, atype: TGrapheneType, label: str) -> TGrapheneType:
        return self._get_from(atype, generate="type", from_source="graphene", label=label)

    def get_graphene_input_type_from_graphene_type(self, atype: TGrapheneType, label: str) -> TGrapheneType:
        return self._get_from(atype, generate="input", from_source="graphene", label=label)

    def get_type_from_graphene_input_type(self, atype: TGrapheneType, label: str) -> TGrapheneType:
        return self._get_from(atype, generate="type", from_source="input", label=label)

    def get_graphene_input_type_from_graphene_input_type(self, atype: TGrapheneType, label: str) -> TGrapheneType:
        return self._get_from(atype, generate="graphene", from_source="input", label=label)

    def _get_from(self, atype: Union[type, TGrapheneType, TGrapheneInputType], generate: str, from_source: str,
                  label: str = None) -> Union[TGrapheneType, TGrapheneInputType]:
        """
        Fetch the default implementation of the input for a given type

        :param atype: type whose input we need to retrieve
        :param from_source: the registry where to ftch data, either "type", "graphene" or "input"
        :param generate: the type to generate. either "type", "graphene" or "input"
        :param label: label rerpesenting the specific association you want to fetch. If None we pick the default one
        :return: an input representing the type
        :raise ValueError: if the type has no known input repersentation
        """
        if from_source == "type":
            if atype not in self._registry_find_by_type:
                raise ValueError(f"Cannot find type that represents the type {atype.__name__}!")
            label_dict = self._registry_find_by_type[atype]
        elif from_source == "graphene":
            if atype not in self._registry_by_graphene_type:
                raise ValueError(f"Cannot find type that represents the graphene type {atype.__name__}!")
            label_dict = self._registry_by_graphene_type[atype]
        elif from_source == "input":
            if atype not in self._registry_by_graphene_input:
                raise ValueError(f"Cannot find type that represents the graphene input type {atype.__name__}!")
            label_dict = self._registry_find_by_type[atype]
        else:
            raise ValueError(f"from_source needs to be either type, graphene or input, not {from_source}!")

        if len(label_dict) == 0:
            raise ValueError(f"there is an error in the registry! There are no slots for type {atype.__name__}!")
        elif len(label_dict) == 1:
            slot = next(iter(label_dict.values()))
        else:
            if label is None:
                # the user has specified no labels. We exploit the OrderDict to get the first slot, which
                # is by definition the default one
                slot = next(iter(label_dict.values()))
            else:
                # fetch the slot requested by the user
                slot = label_dict[label]

        if generate == "type":
            return slot.atype
        elif generate == "graphene":
            return slot.graphene_type
        elif generate == "input":
            return slot.graphene_input_type
        else:
            raise ValueError(f"invalid kind. Either type, graphene or input are accepted, not {generate}!")