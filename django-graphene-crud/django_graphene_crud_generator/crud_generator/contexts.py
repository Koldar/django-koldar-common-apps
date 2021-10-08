from typing import Dict

from django_koldar_utils.graphql_toolsbox.graphql_types import TDjangoModelType, TGrapheneType, TGrapheneInputType

from django_graphene_crud_generator.CrudBuildPhaseEnum import CrudBuildPhaseEnum


class CRUDBuildContext(object):

    def __init__(self, django_type: TDjangoModelType, graphene_type: TGrapheneType,
                 graphene_input_type: TGrapheneInputType, params: Dict[str, any]):
        self.django_type: TDjangoModelType = django_type
        self.graphene_type: TGrapheneType = graphene_type
        self.graphene_input_type: TGrapheneInputType = graphene_input_type

        self.build_phase: CrudBuildPhaseEnum = None

        # self.create_parameters: Dict[str, TGrapheneType] = None
        # self.read_single_parameters: Dict[str, TGrapheneType] = None
        # self.read_all_parameters: Dict[str, TGrapheneType] = None
        # self.update_parameters: Dict[str, TGrapheneType] = None
        # self.delete_parameters: Dict[str, TGrapheneType] = None
        #
        # self.create_return_value: Dict[str, TGrapheneType] = None
        # self.read_single_return_value: Dict[str, TGrapheneType] = None
        # self.read_all_return_value: Dict[str, TGrapheneType] = None
        # self.update_return_value: Dict[str, TGrapheneType] = None
        # self.delete_return_value: Dict[str, TGrapheneType] = None

        self.params: Dict[str, any] = params


class CRUDRuntimeContext(object):
    """
    Information available while running a graphql endpoint
    """

    def __init__(self, c: CRUDBuildContext, info, graphql_class, *args, **kwargs):
        self.crud_build_context = c
        self.info = info
        self.graphql_class = graphql_class
        self.args = args
        self.kwargs = kwargs

    def get_parameter(self, name: str) -> any:
        """
        Scan the graphene query parameters, looking for a parameter named namne

        :param name: name fo the parameter to search
        :return: the value of the parameter, or None if the parameter could not be found
        """
        if name in self.kwargs:
            return self.kwargs[name]
        for x in self.args:
            if isinstance(x, dict) and name in x:
                return x[name]
        else:
            return None
