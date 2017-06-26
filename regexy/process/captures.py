# -*- coding: utf-8 -*-

import collections

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


def capture(char, prev, index=None, is_repeated=False):
    return Capture(
        char=char,
        prev=prev,
        index=index,
        is_repeated=is_repeated)


def _join_reversed(group):
    if group is None:
        return None

    if not group:
        return ''

    if isinstance(group[0], str):
        return ''.join(reversed(group))

    return tuple(
        ''.join(reversed(sub_match))
        for sub_match in reversed(group))


def matched(captured, groups_count):
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
        _join_reversed(match.get(g))
        for g in range(groups_count))
