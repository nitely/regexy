# -*- coding: utf-8 -*-

"""
Tools for creating the capturing\
groups matching results of ``match``\
and friends

:private:
"""

import collections
from typing import (
    Union,
    Tuple,
    Optional)

from ..shared import Symbols


__all__ = [
    'Capture',
    'capture',
    'matched']


Capture = collections.namedtuple('Capture', (
    'char',
    'prev',
    'index',
    'is_repeated'))
Capture.__doc__ = """
    This contains a capture (node)\
    that stores the matched character.\
    The end result can be transversed as\
    a sort of reversed linked-list

    The structure is actually flat since\
    it can only be transversed in reverse,\
    but if there were a way to go forward\
    (which there is not), then the structure\
    would look like a tree containing all\
    matched branches

    There is no distinction between a matched\
    char and start/end group, except the group\
    must have an index and the repeated flag set

    :ivar str char: matched char
    :ivar Capture prev: previous captured char
    :ivar int index: group index
    :ivar bool is_repeated: whether the group\
    is repeated (i.e: has ``*``, ``+``, etc) or not
    :private:
"""


def capture(
        char: str,
        prev: Capture,
        index: int=None,
        is_repeated: bool=False) -> Capture:
    """
    Build a Capture with some optional params

    :private:
    """
    return Capture(
        char=char,
        prev=prev,
        index=index,
        is_repeated=is_repeated)


def _join_reversed(group: list) -> Union[str, Tuple[str]]:
    """
    Reverse-join every match and sub-match

    :param group: a char list of matches\
    and sub-matches
    :return: matched groups as strings\
    or tuple of strings
    :private:
    """
    assert isinstance(group, list)

    if not group:
        return ''

    if isinstance(group[0], str):
        return ''.join(reversed(group))

    return tuple(
        ''.join(reversed(sub_match))
        for sub_match in reversed(group))


MatchedType = Tuple[Union[str, Tuple[str], None]]


def matched(captured: Optional[Capture], groups_count: int) -> MatchedType:
    """
    Construct the matched strings transversing\
    given a captured structure

    The passed Capture has the last captured char\
    and so the sequence is transversed in reverse

    Sub-matches are put in their group index

    Repeating sub-matches (i.e: ``(a)*``) are put\
    into a nested sequence of their group index

    :param captured: The last capture or None
    :param groups_count: number of groups
    :return: matched strings
    :private:
    """
    match = collections.defaultdict(lambda: [])
    curr_groups = []

    while captured:
        if captured.char == Symbols.GROUP_END:
            curr_groups.append(captured)

            if captured.is_repeated:
                match[captured.index].append([])

            captured = captured.prev
            continue

        if captured.char == Symbols.GROUP_START:
            curr_groups.pop()
            captured = captured.prev
            continue

        for g in curr_groups:
            if g.is_repeated:
                match[g.index][-1].append(captured.char)
            else:
                match[g.index].append(captured.char)

        captured = captured.prev

    assert not curr_groups

    return tuple(
        _join_reversed(match[g])
        if g in match
        else None
        for g in range(groups_count))
