import abc
import functools
import re

import graphene
from django_koldar_utils.graphql_toolsbox import graphql_decorators
from django_koldar_utils.graphql_toolsbox.GraphQLHelper import GraphQLHelper

from django_graphene_crud_generator.generator.AbstractGraphQLEndpointGenerator import AbstractGraphQLEndpointGenerator
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext


class AbstractGraphQLQueryGenerator(AbstractGraphQLEndpointGenerator, abc.ABC):
    """
    Generate a query via graphene and automatically registers it with graphql_subquery decorator
    """

    @abc.abstractmethod
    def _get_query_output_name(self, build_context: GraphQLBuildtimeContext) -> str:
        """
        generate the field name in the output that contains the output of the query.
        This value will represents the query **name**!

        :param build_context:context known at build time
        :return: name fo the field
        """
        pass

    @abc.abstractmethod
    def _get_return_value_temp_type_name(self, builld_context: GraphQLBuildtimeContext) -> str:
        pass

    def _compute_graphene_class(self, build_context: GraphQLBuildtimeContext) -> type:
        if isinstance(build_context.action_return_type, graphene.Field):
            # needed otherwise graphene_toolbox.schema will raise an exception
            build_context.action_return_type = build_context.action_return_type.type

        output_name = self._get_query_output_name(build_context)

        assert output_name is not None, f"output name of graphene class \"{build_context.action_class_name}\" is none!"

        doc = re.sub(" +", " ", build_context.action_description)

        def temp_resolver(root, info, *args, temp_resolver_key: str = None, **kwargs):
            # temp resolver has root equal to the query where the temp belongs to
            temp_instance = getattr(root, list(root._meta.fields.keys())[0])
            return getattr(temp_instance, temp_resolver_key)

        def mapper_resolver(root, info, *args, **kwargs):
            nonlocal build_context
            result = build_context.action_body(root, info, *args, **kwargs)
            # we got an instance of the class represented by this query. However, we ned to return a temporary class
            # instance. Note that this is always the case since this mapper is used only when dealing with dictionaries
            temp_class = build_context.get_data("query_temp_class")
            return result

        properties = dict()
        properties["__doc__"] = doc
        build_context.set_data("query_has_temporary_class", False)
        if isinstance(build_context.action_return_type, dict):
            if len(build_context.action_return_type) > 1:
                build_context.set_data("query_has_temporary_class", True)
                # graphene does not support inputting a dict directly. We create a temporary graphene class containign the
                # output of the query
                temp_class_name = self._get_return_value_temp_type_name(build_context)
                temp_properties = dict()
                temp_properties["__doc__"] = f"""Temporary class containing all the output of the query 
                    {build_context.action_class_name}. This class represents the combinations of the fields: 
                    {', '.join(build_context.action_return_type.keys())}.
                """
                for k, v in build_context.action_return_type.items():
                    temp_properties[k] = v
                    temp_properties[f"resolve_{k}"] = functools.partial(temp_resolver, temp_resolver_key=k)

                temp_class = type(
                    temp_class_name,
                    (graphene.ObjectType, ),
                    temp_properties
                )

                build_context.set_data("query_temp_class", temp_class)

                properties[f"resolve_{output_name}"] = mapper_resolver
                properties[output_name] = graphene.Field(temp_class, args=build_context.action_arguments)
            else:
                # dictionary with just a value.
                properties[f"resolve_{output_name}"] = build_context.action_body
                value = list(build_context.action_return_type.values())[0]
                if isinstance(value, graphene.Field):
                    value = value.type
                properties[output_name] = graphene.Field(value, args=build_context.action_arguments)
        else:
            properties[f"resolve_{output_name}"] = build_context.action_body
            value = build_context.action_return_type
            if isinstance(value, graphene.Field):
                value = value.type
            properties[output_name] = graphene.Field(value,
                                                     args=build_context.action_arguments)

        query_class = type(
            build_context.action_class_name,
            (graphene.ObjectType, ),
            properties
        )
        # Apply decorator to auto detect queries
        decorated_query_class = graphql_decorators.graphql_subquery(query_class)

        return query_class