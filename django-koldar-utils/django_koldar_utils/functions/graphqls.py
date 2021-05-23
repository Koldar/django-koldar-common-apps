from graphene_django import DjangoObjectType


def create_graphql_class(cls, fields = None) -> type:
    if fields is None:
        fields = "__all__"
    graphql_type_meta = type(
        "Meta",
        (object, ),
        {
            "model": cls,
            "fields": fields
        }
    )

    class_name = cls.__name__
    graphql_type = type(
        f"{class_name}GraphQLType",
        (DjangoObjectType, ),
        {
            "Meta": graphql_type_meta
        }
    )

    return graphql_type