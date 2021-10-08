def is_function(f) -> bool:
    """
    Check if the passed variable is a function or not

    :param f: function to check
    :return: true if f is a function, false otherwise
    """
    return hasattr(f, "__call__")