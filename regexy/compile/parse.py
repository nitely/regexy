# -*- coding: utf-8 -*-

from ..shared import (
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


def parse(expression):
    return [
        NODES.get(char, CharNode)(char=char)
        for char in expression]


def fill_groups(nodes):
    groups_count = 0
    groups = []

    for index, node in enumerate(nodes):
        if isinstance(node, CharNode) and groups:
            node.is_captured = True
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


def join_atoms(nodes, joiner=Symbols.JOINER):
    """
    Add joiner to regular expression

    Outputs:
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

    """
    atoms_count = 0

    for node in nodes:
        if isinstance(node, CharNode):
            atoms_count += 1

            if atoms_count > 1:
                atoms_count = 1
                yield OpNode(char=joiner)

            yield node
            continue

        if node.char == Symbols.GROUP_START:
            if atoms_count:
                yield OpNode(char=joiner)

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
