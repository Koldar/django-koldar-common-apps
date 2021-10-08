from typing import Union, Dict

import graphene

TDjangoModelType = type
"""
A type that extends models.Model
"""

TGrapheneType = type
"""
A type that represent a graphene_toolbox type object (e.g., AuthorGraphqlType)
"""

TGrapheneInputType = type
"""
A type that extends graphene_toolbox.ObjectInputType
"""

TGrapheneAction = type
"""
A type tha represents either a query or a mutation
"""

TGrapheneQuery = type
"""
A type that represents a grpahql query
"""

TGrapheneMutation = type
"""
A type that rerpesents a grpahql mutation
"""

TGrapheneReturnType = Union[graphene.Scalar, graphene.Field]
"""
A type that is put in graphene_toolbox.ObjectType and represents a query/mutation field
"""

TGrapheneWholeQueryReturnType = Union[TGrapheneReturnType, TDjangoModelType, TGrapheneType, Dict[str, TGrapheneType]]

TGrapheneArgument = Union[graphene.Scalar, graphene.InputObjectType, graphene.Argument]
"""
A type that is put in graphene_toolbox.ObjectType and represents a query/mutation argument
"""