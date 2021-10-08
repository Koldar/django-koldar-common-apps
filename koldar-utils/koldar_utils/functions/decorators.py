import functools
from typing import Callable


def create_stateless_decorator(callable: Callable[["f", "args", "kwargs", "dargs", "dkwargs"], any]):
    """
    Create a decorator which decorates a function.
    It is called stateless because this decorator does not store any information and just call the callable function
    The decorator generated may managed both function args and kwargs and decorator arguments args and kwargs.

    :param callable: a function implementintg th whole decorator. accepts several requried inputs:
        - function to decorate
        - args: *args of the function
        - kwargs: **kwags of the function
        - dargs: *args of the decorator
        - dkwargs: **kwargs of the decorator
        The return value is the value the decorator needs to return
    """

    def stateless_decorator_generator(*decorator_arg, **decorators_kwargs):
        def stateless_decorator(func):
            @functools.wraps(func)
            def wrapper(*func_args, **func_kwargs):
                return callable(func, func_args, func_kwargs, decorator_arg, decorators_kwargs)

            return wrapper

        return stateless_decorator

    return stateless_decorator_generator


def create_stateful_decorator(callable: Callable[[any, "f", "args", "kwargs", "dargs", "dkwargs"], any], state: type = None):
    """
    Create a decorator which decorates a function.
    It is called stateless because this decorator does not store any information and just call the callable function
    The decorator generated may managed both function args and kwargs and decorator arguments args and kwargs.

    :param callable: a function implementintg th whole decorator. accepts several requried inputs:
        - context: an object representing decorator state
        - function to decorate
        - args: *args of the function
        - kwargs: **kwags of the function
        - dargs: *args of the decorator
        - dkwargs: **kwargs of the decorator
        The return value is the value the decorator needs to return
    :param state: type repersenting the context. Needs to have an empty constructor
    """

    def my_decorator(*decorator_arg, **decorators_kwargs):
        def my_decorator(func):
            @functools.wraps(func)
            def wrapper(*func_args, **func_kwargs):
                return callable(wrapper.context, func, func_args, func_kwargs, decorator_arg, decorators_kwargs)

            if not hasattr(wrapper, "context"):
                wrapper.context = state() if state is not None else dict()
            return wrapper

        return my_decorator

    return my_decorator
