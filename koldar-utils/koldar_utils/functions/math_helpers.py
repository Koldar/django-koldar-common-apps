from typing import Union


def bound(x: Union[int, float], lb: Union[int, float], ub: Union[int, float]) -> Union[int, float]:
    """
    Restrict x inside the range [lb, up]
    """
    if x < lb:
        return lb
    if x > ub:
        return ub
    return x


def is_nearly_equal(a, b, abs_tol=1e-3) -> bool:
    """
    True if 2 values (floats) are equal w.r.t. an absolute threshold
    :param a: first value to compare
    :param b: second value to ocmpaer
    :param abs_tol: absolute threshold. default to 1e-3
    :return: true if the 2 values are equal, false otehrwise
    """
    return abs(a-b) <= abs_tol
