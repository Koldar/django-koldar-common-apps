import enum

from django_koldar_utils.models.AbstractEnum import AbstractEnum


class CrudBuildPhaseEnum(AbstractEnum):
    """
    The generators we are currently building in a ICrudGraphQLGenerator
    """
    CREATE = enum.auto()
    READ_SINGLE = enum.auto()
    READ_ALL = enum.auto()
    UPDATE = enum.auto()
    DELETE = enum.auto()
