import json
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django_koldar_utils.django.AbstractDjangoMiddleware import AbstractDjangoMiddleware

import logging

from django_koldar_utils.graphene.AbstractGrapheneMiddleware import AbstractGrapheneMiddleware

from errorcodes_section import error_codes
from graphql_section.types import GraphQLAppError

LOG = logging.getLogger(__name__)


class GraphQLStackTraceInErrorMiddleware(AbstractGrapheneMiddleware):
    """
    A middleware that generates a stacktrace of a backend error. Without this middleware, graphql
    sends just the exception message, not the whole stacktrace
    """

    # def __init__(self, get_response):
    #     super().__init__(get_response)

    #def perform(self, request: "HttpRequest"):
        # response = self.get_response(request)
        # return response

        # if response.headers["Content-Type"] != "application/json":
        #     return response
        # # parse json in content
        # encoding = response.charset or "utf8"
        # str_to_parse = bytes.decode(response.content, response.charset)
        # payload = json.loads(str_to_parse)
        # if "errors" in payload:
        #     payload["sta
        #
        # return response
        # we need to first check that this is a graphql call


    def resolve(self, next, root, info, **kwargs):
         try:
            return next(root, info, **kwargs)
            # graphql response always generate 200 status code
         except Exception as e:
            # a python error has occured. Log the exception and rethrown
            LOG.exception(e)
            raise e
            #raise GraphQLAppError(types.BACKEND_ERROR, exception=str(e))

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        pass

    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        pass