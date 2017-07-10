# -*- coding: utf-8 -*-

"""
Tools for converting an infix regular\
expression into a suffix regex (RPN)

This is based on Shunting-yard algorithm,\
but modified to support regex primitives\
such as groups

:private:
"""

import collections
from typing import (
    Iterator,
    List)

from ..shared.nodes import (
    CharNode,
    Node,
    SymbolNode,
    OpNode)
from ..shared import Symbols


__all__ = ['rpn']


class Associativity:
    """
    Operator associativity. Unary ops are\
    right[-to-left] and binary ops are\
    left[-to-right]

    :ivar int RIGHT: right associativity
    :ivar int LEFT: left associativity
    :private:
    """
    RIGHT, LEFT = range(2)


_Op = collections.namedtuple('Op', (
    'precedence',
    'associativity'))

OPS = {
    Symbols.REPETITION_RANGE: _Op(
        precedence=5,
        associativity=Associativity.RIGHT),
    Symbols.ZERO_OR_ONE: _Op(
        precedence=5,
        associativity=Associativity.RIGHT),
    Symbols.ONE_OR_MORE: _Op(
        precedence=5,
        associativity=Associativity.RIGHT),
    Symbols.ZERO_OR_MORE: _Op(
        precedence=5,
        associativity=Associativity.RIGHT),
    Symbols.JOINER: _Op(
        precedence=4,
        associativity=Associativity.LEFT),
    Symbols.OR: _Op(
        precedence=3,
        associativity=Associativity.LEFT)}


def _has_precedence(a: str, b: str) -> bool:
    """
    Check ``a`` has a higher precedence than ``b``

    Both ``a`` and ``b`` are expected to be valid operator symbols

    Unary operators such as: ``*``, ``?`` and ``+``\
    have right-to-left associativity. Binary operators\
    such as: ``|`` (or) and ``~`` (joiner) have\
    left-to-right associativity

    :param a: Operator symbol to compare
    :param b: Operator symbol to compare against
    :return: Whether a has precedence over b or not
    :private:
    """
    return (
        (OPS[b].associativity == Associativity.RIGHT and
         OPS[b].precedence <= OPS[a].precedence) or
        (OPS[b].associativity == Associativity.LEFT and
         OPS[b].precedence < OPS[a].precedence))


def _pop_greater_than(ops: List[SymbolNode], op: OpNode) -> Iterator[SymbolNode]:
    while (ops and
           ops[-1].char in OPS and
           _has_precedence(ops[-1].char, op.char)):
        yield ops.pop()


def _pop_until_group_start(ops: List[SymbolNode]) -> Iterator[SymbolNode]:
    while True:
        op = ops.pop()
        yield op

        if op.char == Symbols.GROUP_START:
            break


def rpn(nodes: Iterator[Node]) -> Iterator[Node]:
    """
    An adaptation of the Shunting-yard algorithm\
    for producing Reverse Polish Notation out of\
    an expression specified in infix notation

    It supports regex primitives including groups

    The point of doing this is greatly simplifying\
    the parsing of the regular expression into a NFA.\
    Suffix notation removes nesting and so it can\
    be parsed in a linear way instead of recursively (or stack-ily)

    :param nodes: nodes of regex ordered in infix notation
    :return: nodes ordered in suffix notation
    :private:
    """
    operators = []

    for node in nodes:
        if isinstance(node, CharNode):
            yield node
            continue

        if node.char == Symbols.GROUP_START:
            operators.append(node)
            continue

        if node.char == Symbols.GROUP_END:
            yield from _pop_until_group_start(operators)
            yield node
            continue

        if isinstance(node, OpNode):
            yield from _pop_greater_than(operators, node)
            operators.append(node)
            continue

        raise ValueError('Unhandled node: %s' % repr(node))

    yield from reversed(operators)
