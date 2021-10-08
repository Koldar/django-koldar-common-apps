import itertools
from typing import Iterable, Tuple, List


def combinations_of_list(lists: List[Tuple[int, List[any]]]) -> Iterable[Tuple[any]]:
    """
    generate all the combinations of sets

    this is a memory intensvie operation
    """

    # instead of saving all the combiantions in memory, find a way to avoid savigin them to avoid memory consumption

    combinations = [list(itertools.combinations(l, r=r)) for i, (r, l) in enumerate(lists)]
    # now we keep yielding values from the generator
    return itertools.product(*combinations)


def to_tuple(it: Iterable[any], size: int, include_temp_at_end: bool = True, pad_last: bool = True) -> Iterable[any]:
    """
    Convert an iterable into tuples of a specified size

    :param it: iterable to convert
    :param size: size of the tuple to convert
    :param include_temp_at_end: if true, we will yield also the last iterable chunk where there are not enough values
        to form a tuple
    :param pad_last: if true, the last partial tuple will be padded with None values
    """
    tmp_result = []
    for x in it:
        tmp_result.append(x)
        if len(tmp_result) == size:
            yield tuple(tmp_result)
            tmp_result = []
    if include_temp_at_end and len(tmp_result) > 0:
        if pad_last:
            for _ in range(size - len(tmp_result)):
                tmp_result.append(None)
        yield tuple(tmp_result)


def to_pairs(it: Iterable[any], include_temp_at_end: bool = True, pad_last: bool = True) -> Iterable[Tuple[any, any]]:
    yield from to_tuple(it, size=2, include_temp_at_end=include_temp_at_end, pad_last=pad_last)


def to_triples(it: Iterable[any], include_temp_at_end: bool = True, pad_last: bool = True) -> Iterable[Tuple[any, any]]:
    yield from to_tuple(it, size=3, include_temp_at_end=include_temp_at_end, pad_last=pad_last)


def to_shifting_tuple(it: Iterable[any], size: int, include_temp_at_end: bool = True, pad_last: bool = True) -> Iterable[any]:
    """
    Convert an iterable into tuples of a specified size, each yield shifting by a single cell.

    For instance:

    .. :code-block:

        list(iterator_helpers.to_shifting_tuple([0, 1, 2, 3, 4, 5], size=2) # [(0,1), (1, 2), (2, 3), (3, 4), (4, 5)]

    :param it: iterable to convert
    :param size: size of the tuple to convert
    :param include_temp_at_end: if true, we will yield also the last iterable chunk where there are not enough values
        to form a tuple
    :param pad_last: if true, the last partial tuple will be padded with None values
    """
    tmp_result = []
    for x in it:
        if len(tmp_result) == size:
            tmp_result.pop(0)
        tmp_result.append(x)
        if len(tmp_result) == size:
            yield tuple(tmp_result)
    if include_temp_at_end and len(tmp_result) < size:
        if pad_last:
            for _ in range(size - len(tmp_result)):
                tmp_result.append(None)
        yield tuple(tmp_result)


def to_shifting_pairs(it: Iterable[any], include_temp_at_end: bool = True, pad_last: bool = True) -> Iterable[Tuple[any, any]]:
    """
    Convert an iterable into pairs, each yield shifting by a single cell.

    For instance:

    .. :code-block:

        list(iterator_helpers.to_shifting_pairs([0, 1, 2, 3, 4, 5]) # [(0,1), (1, 2), (2, 3), (3, 4), (4, 5)]

    :param it: iterable to convert
    :param size: size of the tuple to convert
    :param include_temp_at_end: if true, we will yield also the last iterable chunk where there are not enough values
        to form a tuple
    :param pad_last: if true, the last partial tuple will be padded with None values
    """
    yield from to_shifting_tuple(it, size=2, include_temp_at_end=include_temp_at_end, pad_last=pad_last)


def to_shifting_triples(it: Iterable[any], include_temp_at_end: bool = True, pad_last: bool = True) -> Iterable[Tuple[any, any]]:
    yield from to_shifting_tuple(it, size=3, include_temp_at_end=include_temp_at_end, pad_last=pad_last)
