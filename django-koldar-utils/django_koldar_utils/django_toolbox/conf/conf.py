from django.utils.module_loading import import_string


def import_from_string(value, setting_name):
    try:
        return import_string(value)
    except ImportError as e:
        raise ImportError(f"Could not import `{value}` for setting `{setting_name}`.`{e.__class__.__name__}`: {e}.")


def get_string_import(obj: any, name: str):
    """
    Check the value associated with name inside the object. If it is a string, the funciton expects it to be a
    a importable string. If this is the case, the fuction also replace the string with the imported content

    :param obj: container
    :param name: field name of obj
    :return: imported concept
    """
    value = getattr(obj, name)
    if isinstance(value, str):
        # replace the string with a callable
        value = import_from_string(value, obj)
        setattr(obj, name, value)
    else:
        return value