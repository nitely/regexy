# -*- coding: utf-8 -*-

import collections

from ..shared import Symbols


__all__ = ['rpn']


class Associativity:

    RIGHT, LEFT = range(2)


_Op = collections.namedtuple('Op', (
    'precedence',
    'associativity'))

OPS = {
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


def _has_precedence(a, b):
    """
    Check ``a`` has a higher precedence than ``b``

    Both ``a`` and ``b`` are expected to be valid operator symbols

    Unary operators such as: ``*``, ``?`` and ``+`` have right-to-left associativity.\
    Binary operators such as: ``|`` (or) and ``~`` (joiner) have left-to-right associativity

    :param str a: Operator symbol to compare
    :param str b: Operator symbol to compare against
    :return: Whether a has precedence over b or not
    """
    return (
        (OPS[b].associativity == Associativity.RIGHT and
         OPS[b].precedence < OPS[a].precedence) or
        (OPS[b].associativity == Associativity.LEFT and
         OPS[b].precedence <= OPS[a].precedence))


def _pop_greater_than(ops, op):
    while (ops and
           ops[-1].char in OPS and
           _has_precedence(ops[-1].char, op.char)):
        yield ops.pop()


def _pop_until_group_start(ops):
    while True:
        op = ops.pop()
        yield op

        if op.char == Symbols.GROUP_START:
            break


def rpn(nodes):
    """
    An adaptation of the Shunting-yard algorithm\
    for producing Reverse Polish notation out of\
    an expression specified in infix notation

    It supports regex primitives including groups
    """
    operators = []

    for node in nodes:
        if node.char == Symbols.GROUP_START:
            operators.append(node)
            continue

        if node.char == Symbols.GROUP_END:
            yield from _pop_until_group_start(operators)
            yield node
            continue

        if node.char in OPS:
            yield from _pop_greater_than(operators, node)
            operators.append(node)
            continue

        yield node

    yield from reversed(operators)
