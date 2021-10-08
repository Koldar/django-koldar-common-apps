import json
from typing import Optional

from django.http import HttpRequest, HttpResponse

import logging

from django_koldar_utils.graphql_toolsbox.graphene_toolbox.AbstractGrapheneMiddleware import AbstractGrapheneMiddleware

LOG = logging.getLogger(__name__)


class GraphQLStackTraceInErrorMiddleware(AbstractGrapheneMiddleware):
    """
    A middleware that generates a stacktrace of a backend error. Without this middleware, graphql
    sends just the exception message, not the whole stacktrace
    """

    def resolve(self, next, root, info, **kwargs):
        try:
            return next(root, info, **kwargs)
            # graphql response always generate 200 status code
        except Exception as e:
            # a python error has occured. Log the exception and rethrown
            LOG.exception(e)
            raise e

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        pass

    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        pass