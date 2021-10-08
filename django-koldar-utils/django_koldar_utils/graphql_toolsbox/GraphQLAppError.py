from typing import Union

from graphql import GraphQLError

from koldar_utils.functions.stacktrace import filter_django_stack
from django_koldar_utils.graphql_toolsbox.ErrorCode import ErrorCode
from django_koldar_utils.graphql_toolsbox.error_codes import BACKEND_ERROR


class GraphQLAppError(GraphQLError):
    """
    A graphql_toolsbox error which has an error code and a dictioanry of involved parameters
    """

    def __init__(self, error: Union[ErrorCode, Exception], **kwargs):
        if isinstance(error, ErrorCode):
            error_code = error
            original_error = None

        elif isinstance(error, Exception):
            error_code = BACKEND_ERROR
            original_error = error
        else:
            raise TypeError(f"Invalid error type. Excpected either an error code or an exception")

        info = dict(
            errorCode=error_code.code,
            params=kwargs,
            stack=filter_django_stack()
        )
        if original_error is not None:
            info["original_error"] = str(original_error)

        super().__init__(
            message=error_code.developer_string,
            original_error=original_error,
            extensions=dict(exceptionInformation=info)
        )
        self.error_code = error_code
        self.param = kwargs

    @classmethod
    def make(cls, error_code: ErrorCode, **kwargs) -> "GraphQLAppError":
        return GraphQLAppError(error_code, **kwargs)

    @classmethod
    def from_exception(cls, e: Exception) -> "GraphQLAppError":
        return GraphQLAppError(e)
