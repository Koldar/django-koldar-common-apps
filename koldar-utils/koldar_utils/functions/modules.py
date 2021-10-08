import importlib
import sys
from typing import Any


def import_module(module_name: str):
    """

    :param module_name: module name to import. It points to a python file. E.g. "com.fibonacci.queries"
    """
    importlib.import_module(module_name)


def add_variable_in_module(module_name: str, variable_name: str, variable_value: Any):
    module = sys.modules[module_name]
    setattr(module, variable_name, variable_value)


def get_variable_in_module(module_name: str, variable_name: str):
    module = sys.modules[module_name]
    return getattr(module, variable_name)


def update_values_in_meta(cls, new_properties) -> type:
    old_meta = cls.__dict__["_meta"]
    print(f"meta values are {old_meta}")
    d = {}
    d.update(new_properties)
    d.update(old_meta.__dict__)

    meta = type("Meta",
        old_meta.bases,
        d
    )
    cls.__dict__["_meta"] = meta
    return meta