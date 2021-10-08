from typing import Callable, Union

from koldar_utils.functions import python_helpers


def implies(x: any, y: Union[Callable[[], bool], any]) -> bool:
    """
    Computes the implication of x to y (x => y).

    Logic table is the following one:

    x | y | x=>y
    ------------
    F | F | V
    F | V | V
    V | F | F
    V | V | V

    :param x: antecendet
    :param y: consequent. May be a callable (useful if the value computation can be done only if the anrtrecedent is true)
    :return: true if x implies y, false otherwise
    """
    if python_helpers.is_function(y):
        if not bool(x):
            return True
        return bool(y())
    else:
        return (not(bool(x))) or (bool(y))
