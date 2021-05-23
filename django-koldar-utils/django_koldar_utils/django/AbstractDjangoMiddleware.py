import abc
from typing import Optional

from django.http import HttpRequest, HttpResponse


class AbstractDjangoMiddleware(abc.ABC):
    """
    A class that allows you to implement a django middleware
    """

    def __init__(self, get_response):
        self.get_response = get_response

    @abc.abstractmethod
    def __call__(self, request: HttpRequest):
        """
        Middleware code execution. To fetch the reposnse, use "self.get_response(request)"

        .. code-block:: python

            response = self.get_response(request)
            return response

        :param request: the HTTP request to fetch the resposne
        :return:
        """
        pass

    @abc.abstractmethod
    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        """

        :param request: request
        :param exception: exception occured
        :return: if none, the default exception handling will kick in. Otherwise we will relay the exception to the next
            middlewares
        """
        pass