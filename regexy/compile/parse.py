# -*- coding: utf-8 -*-

"""
Tools to parse a regular expression into nodes

:private:
"""

from typing import (
    Iterator,
    List,
    Tuple)

from ..shared import nodes
from ..shared import Symbols


__all__ = [
    'parse',
    'fill_groups',
    'join_atoms']


SYMBOLS = {
    Symbols.JOINER: nodes.OpNode,
    Symbols.ZERO_OR_MORE: nodes.OpNode,
    Symbols.ZERO_OR_ONE: nodes.OpNode,
    Symbols.ONE_OR_MORE: nodes.OpNode,
    Symbols.OR: nodes.OpNode,
    Symbols.GROUP_START: nodes.GroupNode,
    Symbols.GROUP_END: nodes.GroupNode,
    Symbols.START: nodes.StartNode,
    Symbols.END: nodes.EndNode,
    Symbols.ANY: nodes.AnyNode}


SHORTHANDS = {
    'w': nodes.AlphaNumNode,
    'd': nodes.DigitNode,
    'W': nodes.NotAlphaNumNode,
    'D': nodes.NotDigitNode}


ASSERTIONS = {
    'b': nodes.WordBoundaryNode}


ESCAPED_CHARS = {**SHORTHANDS, **ASSERTIONS}


def parse_set(expression: Iterator[Tuple[str, str]], *args) -> nodes.SetNode:
    """
    Parse a set atom (``[...]``) into a SetNode

    :param expression: expression iterator\
    beginning after open bracket
    :return: a set node to match against (like any other char node)
    :private:
    """
    char = ''
    chars = []
    ranges = []
    shorthands = []
    is_range = False
    is_escaped = False

    for char, _nxt in expression:
        if (char == ']' and
                not is_escaped and
                (chars or ranges or shorthands)):
            break

        if char == '\\' and not is_escaped:
            is_escaped = True
            continue

        if is_range:
            is_escaped = False
            is_range = False
            ranges.append(
                (chars.pop(), char))
            continue

        if is_escaped:
            is_escaped = False

            if char in SHORTHANDS:
                shorthands.append(
                    SHORTHANDS[char](char=char).char)
            else:
                chars.append(char)

            continue

        if char == '-' and chars:
            is_range = True
            continue

        chars.append(char)

    if is_range:
        chars.append('-')

    assert not is_escaped
    assert chars or ranges or shorthands
    assert char == ']'

    return nodes.SetNode(
        chars=chars,
        ranges=ranges,
        shorthands=shorthands)


def parse_repetition_range(
        expression: Iterator[Tuple[str, str]],
        *args) -> nodes.RepetitionRangeNode:
    start = []
    end = []
    curr = start

    for char, _nxt in expression:
        if char == '}':
            break

        if char == ',':
            assert curr == start
            curr = end
            continue

        assert '0' <= char <= '9'
        curr.append(char)

    if curr == start:
        end = start

    start = int(''.join(start) or 0)

    if end:
        end = int(''.join(end) or 0)
    else:
        end = None

    return nodes.RepetitionRangeNode(
        char=Symbols.REPETITION_RANGE,
        start=start,
        end=end)


def parse_group_tag(expression: Iterator[Tuple[str, str]], next_char: str) -> nodes.GroupNode:
    if next_char != '?':
        return nodes.GroupNode(char=Symbols.GROUP_START)

    # At the moment this is just for non-capturing group
    next(expression)
    char, _nxt = next(expression)
    assert char == ':'
    return nodes.GroupNode(
        char=Symbols.GROUP_START,
        is_capturing=False)


SUB_PARSERS = {
    '[': parse_set,
    '{': parse_repetition_range,
    Symbols.GROUP_START: parse_group_tag}


def _peek(iterator, eof=None):
    """
    Return an iterator

    Yield current value and\
    next value in each iteration

    :private:
    """
    iterator = iter(iterator)

    try:
        prev = next(iterator)
    except StopIteration:
        return iterator

    for elm in iterator:
        yield prev, elm
        prev = elm

    yield prev, eof


def parse(expression: str) -> Iterator[nodes.Node]:
    """
    Parse a regular expression into a sequence nodes.\
    Literals (escaped chars) are parsed as shorthands\
    (if found) or as regular char nodes.\
    Symbols (``*``, etc) are parsed into symbol nodes.\
    Same for groups. Sets are parsed into set nodes.

    :param expression: regular expression
    :return: iterator of nodes
    :private:
    """
    expression = _peek(iter(expression))
    is_escaped = False

    for char, next_char in expression:
        if is_escaped:
            is_escaped = False
            yield ESCAPED_CHARS.get(char, nodes.CharNode)(char=char)
            continue

        if char == '\\':
            is_escaped = True
            continue

        if char in SUB_PARSERS:
            yield SUB_PARSERS[char](expression, next_char)
            continue

        yield SYMBOLS.get(char, nodes.CharNode)(char=char)

    assert not is_escaped


def greediness(expression_nodes: Iterator[nodes.Node]) -> Iterator[nodes.Node]:
    nodes_it = _peek(expression_nodes)

    for node, next_node in nodes_it:
        # todo: make RepetitionNode?
        is_repetition = (
            isinstance(node, nodes.OpNode) and
            node.char in (
                Symbols.ZERO_OR_ONE,
                Symbols.ZERO_OR_MORE,
                Symbols.ONE_OR_MORE,
                Symbols.REPETITION_RANGE))
        is_next_zero_or_one = (
            isinstance(next_node, nodes.OpNode) and
            next_node.char == Symbols.ZERO_OR_ONE)

        if is_repetition and is_next_zero_or_one:
            node.is_greedy = True
            next(nodes_it)  # Skip next

        yield node


def join_atoms(expression_nodes: Iterator[nodes.Node]) -> Iterator[nodes.Node]:
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

    :param nodes: an iterator of nodes
    :return: iterator of nodes containing joiners
    :private:
    """
    atoms_count = 0

    for node in expression_nodes:
        if isinstance(node, (nodes.CharNode, nodes.AssertionNode)):
            atoms_count += 1

            if atoms_count > 1:
                atoms_count = 1
                yield nodes.OpNode(char=Symbols.JOINER)

            yield node
            continue

        if node.char == Symbols.GROUP_START:
            if atoms_count:
                yield nodes.OpNode(char=Symbols.JOINER)

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
                Symbols.ZERO_OR_ONE,
                Symbols.REPETITION_RANGE}:
            atoms_count += 1
            yield node
            continue

        raise ValueError('Unhandled node %s' % repr(node))


def fill_groups(expression_nodes: List[nodes.Node]) -> int:
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
    groups_non_capt = []

    for index, node in enumerate(expression_nodes):
        if isinstance(node, nodes.CharNode):
            node.is_captured = len(groups) - len(groups_non_capt) > 0
            continue

        if node.char == Symbols.GROUP_START:
            assert isinstance(node, nodes.GroupNode)

            if not node.is_capturing:
                groups_non_capt.append(node)
                groups.append(node)
                continue

            node.index = groups_count
            groups_count += 1
            groups.append(node)
            continue

        if node.char == Symbols.GROUP_END:
            start = groups.pop()

            if not start.is_capturing:
                groups_non_capt.pop()
                node.is_capturing = False
                continue

            try:
                next_node = expression_nodes[index + 1]
            except IndexError:
                start.is_repeated = False
            else:
                start.is_repeated = next_node.char in (
                    Symbols.ZERO_OR_MORE,
                    Symbols.ONE_OR_MORE,
                    Symbols.REPETITION_RANGE)

            node.index = start.index
            node.is_repeated = start.is_repeated

    assert not groups

    return groups_count
