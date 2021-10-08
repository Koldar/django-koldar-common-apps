import abc
import functools
import inspect
import logging
from typing import Dict, Union, Callable, List, Tuple

import graphene
import graphene_django

from django_koldar_utils.graphql_toolsbox import graphql_decorators
from django_koldar_utils.graphql_toolsbox.graphql_types import TGrapheneInputType, TGrapheneType, TDjangoModelType, \
    TGrapheneQuery, TGrapheneArgument, TGrapheneWholeQueryReturnType
from koldar_utils.models.AbstractEnum import AbstractEnum

from django_graphene_crud_generator.IGraphQLEndpointComponent import IGraphQLEndpointComponent
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext

LOG = logging.getLogger(__name__)


class ComponentPriorityEnum(AbstractEnum):
    HIGH_09 = -900
    HIGH_08 = -800
    HIGH_07 = -700
    HIGH_06 = -600
    HIGH_05 = -500
    HIGH_04 = -400
    HIGH_03 = -300
    HIGH_02 = -200
    HIGH_01 = -100
    NORMAL = +000
    LOW_01 = +100
    LOW_02 = +200
    LOW_03 = +300
    LOW_04 = +400
    LOW_05 = +500
    LOW_06 = +600
    LOW_07 = +700
    LOW_08 = +800
    LOW_09 = +900

    def __int__(self):
        return int(self.value)


class AbstractGraphQLEndpointGenerator(IGraphQLEndpointComponent, abc.ABC):
    """
    Generate a mutation/query endpoint
    """

    def __init__(self):
        self.__components: List[Tuple[int, IGraphQLEndpointComponent]] = []

    @property
    def components(self):
        return list(map(lambda x: x[1], self.__components))

    def register_component(self, *components: IGraphQLEndpointComponent, priority: int = 0):
        """
        Register a component (or more than 1). A component is an additional class that can be used to agument
        this generator.
        It is like a mixin, but can be programmatically added and removed as the developer wishes.

        Do not rely on the stability of the sorting algorithm: Components with the same priority have their order of
        calling without garantees.
        :param components: compoenents to register
        :param priority: the priority of the component. small priorities (even neative) are computed first w.r.t greater
            priority. In case you don't know which priority apply, 0 is a sane default. For some typical priorities,
            consider using ComponentPriorityEnum enum
        """
        for x in components:
            self.__components.append((int(priority), x))
        # now sort the componenets. It is CPU wasteful, but i think i will have at most 100 components per generator
        self.__components.sort(key=lambda x: int(x[0]))

    def clear_components(self):
        self.__components.clear()

    def call_component_method_with_result_store(self, name: str, build_context: GraphQLBuildtimeContext, args: List[str] = None, kwargs: Dict[str, any] = None, accumulate: Callable[[List[any], Dict[str, any], any], Tuple[List[any], Dict[str, any]]] = None, default_return_value: any = None):
        """
        Scans all the components of this class and iteratively call the method with the specified name.
        If accumulate is defined, you can use the return value fo the method called to alter args and kwargs of the next method call.
        if a component does not have the specified method, we will skip ahead.

        This method is different than call_component_method becuase each time a result from a component is fetched, we
        store its value in build_context "data" section under the key "f{name}_result" where name is the method name.
        The key is then removed at the end of this method

        :param name: name of the method to call
        :param accumulate: function that is used to integrate the return value of a component method jkust called to
            alter args and kwargs of the next component call. The last accumulate call we perform will not change
            anything
        :param default_return_value: value to return if no component has the specified method. Defaults to None
        :param args: initial arg of the first component method invocation
        :param kwargs: initial kwarg of the first component method invocation
        :return: return value of the component call
                """

        data_key = f"{name}_result"

        def wrapper_accumulate(_args, _kwargs, _result):
            nonlocal build_context
            if accumulate is not None:
                _args, _kwargs = accumulate(_args, _kwargs, _result)
            build_context.set_data(data_key, _result)
            return _args, _kwargs

        try:
            return self.call_component_method(
                name=name,
                args=args,
                kwargs=kwargs,
                accumulate=wrapper_accumulate,
                default_return_value=default_return_value
            )
        finally:
            build_context.delete_data(data_key)

    def call_component_method(self, name: str, args: List[any] = None, kwargs: Dict[str, any] = None, accumulate: Callable[[List[any], Dict[str, any], any], Tuple[List[any], Dict[str, any]]] = None, default_return_value: any = None) -> any:
        """
        Scans all the components of this class and iteratively call the method with the specified name.
        If accumulate is defined, you can use the return value fo the method called to alter args and kwargs of the next method call.
        if a component does not have the specified method, we will skip ahead

        :param name: name of the method to call
        :param accumulate: function that is used to integrate the return value of a component method jkust called to
            alter args and kwargs of the next component call. The last accumulate call we perform will not change
            anything
        :param default_return_value: value to return if no component has the specified method. Defaults to None
        :param args: initial arg of the first component method invocation
        :param kwargs: initial kwarg of the first component method invocation
        :return: return value of the component call
        """

        if args is None:
            args = []
        if kwargs is None:
            kwargs = dict()
        result = default_return_value
        for x in self.components:
            if not hasattr(x, name):
                continue
            result = getattr(x, name)(*args, **kwargs)
            if accumulate is not None:
                args, kwargs = accumulate(args, kwargs, result)
        return result



    @abc.abstractmethod
    def _compute_graphene_class(self, build_context: GraphQLBuildtimeContext) -> type:
        """
        Function used to generate a class that represents a graphene query
        """
        pass

    @abc.abstractmethod
    def graphql_body_function(self, runtime_context: GraphQLRuntimeContext, *args, **kwargs) -> TGrapheneWholeQueryReturnType:
        """
        A function that is called when the graphql endpoint is invoked. The output is the return valu that you want to
        pass to graphene.
        :param runtime_context: information known at runtime
        :param args: graphql arguments
        :param kwargs: graphql arguments
        :return: return value to pass to graphene
        """
        pass

    def _check_input_parameters(self, build_context: GraphQLBuildtimeContext):
        """
        perform some checks to ensure the input type for this type is correct
        :param build_context: parameters to check
        :return:
        """
        pass

    def generate(self, **kwargs) -> TGrapheneQuery:
        """
        Allows you to create a graphql endpoint in a easy manner

        :param kwargs: parameters implementatio dependent. The user can use these to pass important data to the implementation
        :return: a class representing a callable from graphql
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

        build_context = GraphQLBuildtimeContext(
            params=kwargs
        )

        # arguments
        build_context.action_arguments = dict()
        _, build_context.action_arguments = self._generate_action_arguments(build_context)
        for x in self.components:
            if hasattr(x, "_generate_action_arguments"):
                op, args = x._generate_action_arguments(build_context)
                if op == "update":
                    build_context.action_arguments.update(args)
                elif op == "set":
                    build_context.action_arguments = args
                elif op == "subtract":
                    for k in args.keys():
                        del build_context.action_arguments[k]
                else:
                    raise ValueError(f"invalid operation {op} when dealing with arguments of component {x}")

        # return type
        build_context.action_return_type = dict()
        _, build_context.action_return_type = self._generate_action_return_type(build_context)
        for x in self.components:
            if hasattr(x, "_generate_action_return_type"):
                op, args = x._generate_action_return_type(build_context)
                if op == "update":
                    build_context.action_return_type.update(args)
                elif op == "set":
                    build_context.action_return_type = args
                elif op == "subtract":
                    for k in args.keys():
                        del build_context.action_return_type[k]
                else:
                    raise ValueError(f"invalid operation {op} when dealing with return values of {x}")

        # endpoint class name
        build_context.action_class_name = self._generate_action_class_name(build_context)
        for x in self.components:
            if hasattr(x, "_generate_action_class_name"):
                build_context.action_class_name = x._generate_action_class_name(build_context)

        build_context.action_description = []
        build_context.action_description = self._generate_action_description(build_context)
        for x in self.components:
            if hasattr(x, "_generate_action_description"):
                for y in x._generate_action_description(build_context):
                    build_context.action_description.append(y)
        build_context.action_description = "\n".join(build_context.action_description)

        assert build_context.action_class_name is not None, "Query class name is None"
        assert all(map(lambda x: x is not None, build_context.action_arguments.keys())), f"Some arguments of {build_context.action_class_name} are None"
        assert build_context.action_return_type is not None, f"return type of {build_context.action_class_name} is None"
        assert build_context.action_description is not None, f"description of {build_context.action_class_name} is None"
        self._check_input_parameters(build_context)
        assert (not inspect.isclass(build_context.action_return_type)) or (issubclass(build_context.action_return_type, (graphene.Scalar, graphene.ObjectType, graphene_django.DjangoObjectType))), \
            f"return type \"{build_context.action_return_type}\" of \"{build_context.action_class_name}\" cannot be a type subclass graphene_toolbox.Field, but needs to be a plain ObjectType!"
        assert ((inspect.isclass(build_context.action_return_type)) or (isinstance(build_context.action_return_type, (graphene.List, graphene.Field, dict)))), \
            f"return type \"{build_context.action_return_type}\" of \"{build_context.action_class_name}\" cannot be an instanc deriving graphene_toolbox.Field, but needs to be a plain ObjectType!"

        def perform_query(root, info, *args, **kwargs) -> any:

            nonlocal build_context

            def invoke_generator_body_from_graphene_basic():
                def decorator(generator_body):
                    @functools.wraps(generator_body)
                    def wrapper(*aargs, **akwargs):
                        nonlocal runtime_context
                        # generator_body has the signature runtime_context, *args, **kwargs
                        result = generator_body(runtime_context, *runtime_context.args, **runtime_context.kwargs)
                        return result

                    return wrapper

                return decorator

            def invoke_graphene_basic_from_generator_body():
                def decorator(graphene_resolve):
                    @functools.wraps(graphene_resolve)
                    def wrapper(*aargs, **akwargs):
                        nonlocal runtime_context
                        # graphene_resolve has the signature cls, info, *args, **kwargs
                        result = graphene_resolve(runtime_context.root, runtime_context.info, *runtime_context.args,
                                   **runtime_context.kwargs)
                        return result

                    return wrapper

                return decorator

            if root is None:
                root = build_context.action_class

            runtime_context = GraphQLRuntimeContext(build_context, root, info, *args, **kwargs)
            LOG.info(f"Computing result for graphql query {build_context.action_class_name}...")

            body = self.graphql_body_function
            dec = self._graphql_body_function_decorator(runtime_context)
            if dec is not None:
                body = dec(body)
            for x in self.components:
                if hasattr(x, "_graphql_body_function_decorator_native"):
                    dec = x._graphql_body_function_decorator_native(runtime_context)
                    if dec is not None:
                        # the decorator "dec" assumes that body follows the signature cls, info, *args, **kwargs, which
                        # it does not. So we need to convert "body" into a a function using that signature first
                        body = dec(invoke_generator_body_from_graphene_basic()(body))
                        # _graphql_body_function_decorator_native returns a GrapheneBodyFunction, not a
                        # GrapheneGeneratorBodyFunction so we need to a mapper to convert GrapheneBodyFunction
                        # into GrapheneGeneratorBodyFunction again to avoid the chain to be broken
                        body = invoke_graphene_basic_from_generator_body()(body)

                if hasattr(x, "_graphql_body_function_decorator"):
                    dec = x._graphql_body_function_decorator(runtime_context)
                    if dec is not None:
                        body = dec(body)
            result = body(runtime_context, *args, **kwargs)

            LOG.info(f"returning to graphene as the request {root} the value {result} (type {type(result)})")
            return result

        build_context.action_body = perform_query

        result_class = self._compute_graphene_class(build_context)
        build_context.action_class = result_class
        return result_class
