from typing import Dict

from graphene import ObjectType

from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneInputType, TGrapheneType, TDjangoModelType, \
    TGrapheneAction

from django_graphene_crud_generator.types import GrapheneGeneratorBodyFunction


class GraphQLBuildtimeContext(object):
    """
    Contains all the information available during compile time
    """

    def __init__(self, params: Dict[str, any]):
        self.action_arguments = dict()
        self.action_return_type = None
        self.action_class_name = None
        self.action_description = None
        self.action_body: GrapheneGeneratorBodyFunction = None
        self.action_class: TGrapheneAction = None

        self.__internal_data = {}
        self.params = params

    def get_data(self, name: str) -> any:
        """
        Sometimes you need to use transfer some information from one component to another one. Use this method to do
        so. We simply map a dictionary
        :param name: name fo the data to retrieve
        :return: data retrieved
        """
        return self.__internal_data[name]

    def set_data(self, name: str, value: any):
        """
        Sometimes you need to use transfer some information from one component to another one. Use this method to do
        so. We simply map a dictionary
        :param name: name fo the data to store
        :param value: value of the data to store
        :return:
        """
        self.__internal_data[name] = value

    def delete_data(self, name: str):
        """
        Delete a data from the build context. if the key is not present we do nothing

        :param name: name fo the data to delete
        """
        if name in self.__internal_data:
            del self.__internal_data[name]

    def has_data(self, name: str) -> bool:
        """
        Check if we have set the specific name
        :param name:
        :return:
        """
        return name in self.__internal_data


    def get_param(self, name: str) -> any:
        if name not in self.params:
            raise KeyError(f"""We tried to gain access to the graphql endpoint generator parameter named \"{name}\", 
                but the user did not set it while calling generate function. Recheck.""")
        return self.params[name]

    def is_param_present(self, *names: str) -> bool:
        """
        Check if several parameter are present in the param dictionary
        """

        return all(map(lambda x: x in self.params, names))


class GraphQLRuntimeContext(object):
    """
    Contains all the data that we know in runtime
    """

    def __init__(self, build_context: GraphQLBuildtimeContext, root: any, info: any, *args, **kwargs):
        self.build_context = build_context
        """
        object used to get the information known at compile time
        """
        self.root = root
        """
        graphql parent resolver
        """
        self.info = info
        """
        graphql info instance
        """
        self.args = args
        """
        graphql args variable
        """
        self.kwargs = kwargs
        """
        graphql args variable
        """
        self.params: Dict[str, any] = dict()
        """
        Additional data the runtime has
        """

    def get_param(self, name: str) -> any:
        return self.params[name]

    def set_param(self, name: str, value: any):
        self.params[name] = value

    def get_input(self, name: str) -> ObjectType:
        """
        Fetch a graphql input parameter from the args and kwargs of the graphql query

        :param name: name of the parameter to fetch
        :return: value of the parameter
        """
        if name in self.kwargs:
            return self.kwargs[name]
        for x in self.args:
            if isinstance(x, tuple) and x[0] == name:
                return x[1]
        raise KeyError(f"Could not found the parameter {name} in the graphql arguments: args={self.args} kwargs={self.kwargs}")
