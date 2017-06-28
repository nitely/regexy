# -*- coding: utf-8 -*-

"""
Tools for compiling a regular expression\
into some of the in-between conversions\
from infix regular expression to NFA

The compiling steps are not made for\
performance but for readability and maintainability.\
This is mostly because resulting NFAs should be\
compiled once and cached on import time.\
One-off scripts are not a use-case I care about

:public:
"""

import collections

from .parse import (
    parse,
    fill_groups,
    join_atoms)
from .rpn import rpn
from .nfa import nfa


__all__ = [
    'NFA',
    'to_nfa',
    'to_rpn',
    'to_atoms']


NFA = collections.namedtuple('NFA', (
    'state',
    'groups_count'))
NFA.__doc__ = """
    This contains the first state\
    of the NFA and the number of groups

    The state must be treated as an immutable data\
    structure, but currently this is not enforced

    :ivar Node state: the first node of the NFA
    :ivar int groups_count: the number of capturing groups
    :private:
"""


def to_nfa(expression: str) -> NFA:
    """
    Build the NFA from a given regular expression

    This should be cached at the app level\
    when performance matters

    It's thread safe

    :param expression: regex expression
    :return: NFA for the given expression
    :public:
    """
    nodes = parse(expression)
    groups_count = fill_groups(nodes)
    return NFA(
        state=nfa(rpn(join_atoms(nodes))),
        groups_count=groups_count)


def to_rpn(expression: str) -> str:
    """
    Convert a regular expression infix notation into suffix notation

    This is mostly for testing purposes\
    and not meant to be used as a public API

    :param expression: regular expression in infix notation
    :return: regular expression in suffix notation (RPN)
    :private:
    """
    return ''.join(
        node.char
        for node in rpn(join_atoms(parse(expression))))


def to_atoms(expression: str) -> str:
    """
    Add joiners to a regular expression

    This is mostly for testing purposes\
    and not meant to be used as a public API

    :param expression: regular expression
    :return: regular expression with joiners
    :private:
    """
    return ''.join(
        node.char
        for node in join_atoms(parse(expression)))

