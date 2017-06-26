# -*- coding: utf-8 -*-

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


def to_nfa(expression):
    nodes = parse(expression)
    groups_count = fill_groups(nodes)
    return NFA(
        state=nfa(rpn(join_atoms(nodes))),
        groups_count=groups_count)


def to_rpn(expression):
    return ''.join(
        node.char
        for node in rpn(join_atoms(parse(expression))))


def to_atoms(expression):
    return ''.join(
        node.char
        for node in join_atoms(parse(expression)))

