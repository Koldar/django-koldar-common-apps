from django_koldar_utils.graphql_toolsbox.graphql_types import TDjangoModelType

from django_graphene_crud_generator.IGraphQLEndpointComponent import IGraphQLEndpointComponent
from django_graphene_crud_generator.crud_generator.contexts import CRUDBuildContext, CRUDRuntimeContext
from django_graphene_crud_generator.crud_generator.mixins import AddCRUDContextComponentMixIn
from django_graphene_crud_generator.generator.contexts import GraphQLBuildtimeContext, GraphQLRuntimeContext



class AbstractGraphQLCrudComponent(AddCRUDContextComponentMixIn, IGraphQLEndpointComponent):
    """
    Components using this class will be able to gain access to both CRUD build and runtime
    context
    """
    pass

