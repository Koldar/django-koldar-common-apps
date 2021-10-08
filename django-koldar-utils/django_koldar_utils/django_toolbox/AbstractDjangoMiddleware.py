import abc
from typing import Optional

from django.http import HttpRequest, HttpResponse


class AbstractDjangoMiddleware(abc.ABC):
    """
    A class that allows you to implement a django_toolbox middleware
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        return self.perform(request)

    @abc.abstractmethod
    def perform(self, request: "HttpRequest"):
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
    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        """
        Called just before a django_toolbox view is called.
        """
        pass

    @abc.abstractmethod
    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        """
        Django calls process_exception() when a view raises an exception.
        process_exception() should return either None or an HttpResponse object.
        If it returns an HttpResponse object, the template response and response middleware will be
        applied and the resulting response returned to the browser. Otherwise, default exception handling kicks in.

        Again, middleware are run in reverse order during the response phase, which includes process_exception.
        If an exception middleware returns a response, the process_exception methods of the middleware
        classes above that middleware won’t be called at all.

        :param request: request
        :param exception: exception occured
        :return: if none, the default exception handling will kick in. Otherwise we will relay the exception to the next
            middlewares
        """
        pass