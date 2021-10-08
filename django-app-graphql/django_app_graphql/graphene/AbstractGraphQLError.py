from graphql import GraphQLError


class AbstractGraphQLError(GraphQLError):
    """
    A graphql error that send several inputs to the client. In order to use it, just derive the class
    """
    def __init__(self, error_code: any, **kwargs):
        super().__init__(
            message=f"Code={int(error_code):04d} ({str(error_code)})",
            extensions=dict(kwargs)
        )
        self.code = error_code

    def __str__(self) -> str:
        return f"Code={int(self.code):04d} ({str(self.code)}) data={self.extensions}"


class StandardGraphQLError(AbstractGraphQLError):
    """
    If you are too lazy to derive AbstractGraphQLError for every project, just use this
    """
    pass

