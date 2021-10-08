import abc


class AbstractGrapheneMiddleware(abc.ABC):
    """
    Middleware specific for graphene_toolbox
    """

    def __init__(self):
        pass

    @abc.abstractmethod
    def resolve(self, next, root, info, **kwargs):
        """
        Perform an action in the middleware.

        :param next: function used to forward the request to the enxt graphene_toolbox middleware. To do so, code "next(root, info, **kwargs)"
        :param info: information that can be used to retrieve context (i.e., info.context) or path (i.e., info.path)
        :param root: query root
        :param kwargs: other key work parameters
        """
        pass
