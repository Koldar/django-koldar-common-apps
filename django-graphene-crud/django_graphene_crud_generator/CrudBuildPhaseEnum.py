import enum

from koldar_utils.models.AbstractEnum import AbstractEnum


class CrudBuildPhaseEnum(AbstractEnum):
    """
    The generators we are currently building in a AbstractCrudGraphQLGenerator
    """
    CREATE = enum.auto()
    READ_SINGLE = enum.auto()
    READ_ALL = enum.auto()
    UPDATE = enum.auto()
    DELETE = enum.auto()
