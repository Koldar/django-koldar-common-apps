import abc
from django.db import models


class AbstractModelMetaclass(abc.ABCMeta, type(models.Model)):
    """
    Class which can be used to provide abc abstract methods and django_toolbox models

    .. ::code-block:: python
        class AbstractModel(models.Model, metaclass=AbstractModelMetaclass):
            # You may have common fields here.

            class Meta:
                abstract = True

            @abc.abstractmethod
            def must_implement(self):
                pass


        class MyModel(AbstractModel):
            code = models.CharField("code", max_length=10, unique=True)

            class Meta:
                app_label = 'my_app'

    :see https://stackoverflow.com/a/66888176/1887602:
    """

    pass