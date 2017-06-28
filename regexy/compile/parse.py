# -*- coding: utf-8 -*-

"""
Tools to parse a regular expression into nodes

:private:
"""

from typing import (
    Iterator,
    List)

from ..shared import (
    Node,
    OpNode,
    GroupNode,
    CharNode,
    Symbols)


__all__ = [
    'parse',
    'fill_groups',
    'join_atoms']


NODES = {
    Symbols.JOINER: OpNode,
    Symbols.ZERO_OR_MORE: OpNode,
    Symbols.ZERO_OR_ONE: OpNode,
    Symbols.ONE_OR_MORE: OpNode,
    Symbols.OR: OpNode,
    Symbols.GROUP_START: GroupNode,
    Symbols.GROUP_END: GroupNode}


def _parse(expression: str) -> Iterator[Node]:
    """
    Parse a regular expression into a sequence nodes.\
    Literals (escaped chars) are parsed as shorthands\
    (if found) or as regular char nodes.\
    Symbols (``*``, etc) are parsed into symbol nodes.\
    Same for groups.

    :param expression: regular expression
    :return: iterator of nodes
    :private:
    """
    escape = False

    for char in expression:
        if escape:
            escape = False
            yield CharNode(char=char)
            continue

        if char == '\\':
            escape = True
            continue

        yield NODES.get(char, CharNode)(char=char)


def parse(expression: str) -> List[Node]:
    """
    Parse a regular expression into nodes

    :param expression: regular expression
    :return: list of nodes
    :private:
    """
    return list(_parse(expression))


def fill_groups(nodes: List[Node]) -> int:
    """
    Fill groups with missing data.\
    This is index of group, whether\
    is a repeat group or not and capturing\
    flag for chars within the group

    This is required for later capturing of\
    characters when searching/matching a text

    :param nodes: a list of nodes
    :return: number of groups
    :private:
    """
    groups_count = 0
    groups = []

    for index, node in enumerate(nodes):
        if isinstance(node, CharNode):
            node.is_captured = bool(groups)
            continue

        if node.char == Symbols.GROUP_START:
            node.index = groups_count
            groups.append(node)
            groups_count += 1
            continue

        if node.char == Symbols.GROUP_END:
            try:
                next_node = nodes[index + 1]
            except IndexError:
                is_repeated = False
            else:
                is_repeated = next_node.char in (
                    Symbols.ZERO_OR_MORE,
                    Symbols.ONE_OR_MORE)

            start = groups.pop()
            start.is_repeated = is_repeated

            node.index = start.index
            node.is_repeated = start.is_repeated

    assert not groups

    return groups_count


def join_atoms(nodes: Iterator[Node]) -> Iterator[Node]:
    """
    Add joiners to a sequence of nodes.\
    Joiners are meant to join sets\
    of chars that belong together.\
    This is required for later conversion into rpn notation.

    To clarify why this is necessary say there\
    is a math formula (not a regex) such as ``1+2``.\
    In RPN this would read as ``12+``.\
    Now what about ``11+12``? without joiners this would\
    read ``1112+`` and would be wrongly executed as ``111+2``.\
    Enter joins the RPN is ``1~11~2+`` and the parser\
    will know ``1~1`` means ``11`` and\
    ``1~2`` means ``12`` resulting in ``11+12``.

    Outputs::

        a~(b|c)*~d
        (a~b~c|d~f~g)
        a~b~c
        (a~b~c|d~e~f)*~x~y~z
        a+~b
        a?~b
        a*~b
        a+~b?
        (a)~(b)
        (a)~b

    :param nodes: a iterator of nodes
    :return: iterator of nodes containing joiners
    :private:
    """
    atoms_count = 0

    for node in nodes:
        if isinstance(node, CharNode):
            atoms_count += 1

            if atoms_count > 1:
                atoms_count = 1
                yield OpNode(char=Symbols.JOINER)

            yield node
            continue

        if node.char == Symbols.GROUP_START:
            if atoms_count:
                yield OpNode(char=Symbols.JOINER)

            atoms_count = 0
            yield node
            continue

        if node.char == Symbols.OR:
            atoms_count = 0
            yield node
            continue

        if node.char in {
                Symbols.GROUP_END,
                Symbols.ZERO_OR_MORE,
                Symbols.ONE_OR_MORE,
                Symbols.ZERO_OR_ONE}:
            atoms_count += 1
            yield node
            continue

        raise ValueError('Unhandled node %s' % repr(node))
