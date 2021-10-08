import abc

from django.utils.deconstruct import deconstructible


@deconstructible
class AbstractValidator(abc.ABC):
    """
    A generic validator.
    Be sure to decorate the derived class with "@deconstructible"!
    """

    @abc.abstractmethod
    def validate(self, value_to_check):
        """
        Validate a value against this validation rule. If the validation fails, a ValidationError needs to be generated

        :param value_to_check: the value to check
        :raises ValidationError: if the validation fails
        """
        pass

    def __call__(self, *args, **kwargs):
        return self.validate(args[0])

    @abc.abstractmethod
    def __eq__(self, other):
        """
        Check if an instance of a validator is
        """
        pass


@deconstructible
class AbstractStatelessValidator(AbstractValidator, abc.ABC):
    """
    If the validator has no internal state you might want to use this class. It allows to generate a validator miore easily.
    Be sure to decorate the derived class with "@deconstructible"!
    """

    def __eq__(self, other):
        return isinstance(other, type(self))
