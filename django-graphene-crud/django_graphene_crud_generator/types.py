from typing import Callable, List, Dict

GrapheneGeneratorBodyFunction = Callable[["GraphQLRuntimeContext", List[any], Dict[str, any]], any]
"""
type fo graphene body function. Specific of IgraphQLEndpointGenerator
"""

GrapheneBodyFunction = Callable[[any, any, List[any], Dict[str, any]], any]
"""
type of grapghene boduy function. Compliant with graphene mutate/resolve methods
"""