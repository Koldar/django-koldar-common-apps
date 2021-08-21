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
