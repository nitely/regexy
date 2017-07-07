# -*- coding: utf-8 -*-

"""
Tools for creating the NFA states

:private:
"""

import copy
from typing import (
    Iterator,
    Tuple)

from ..shared import (
    Node,
    EOF,
    CharNode,
    Symbols,
    RepetitionRangeNode,
    OpNode)


__all__ = ['nfa']


def _dup(state: Node, visited: set=None) -> Node:
    assert isinstance(state, Node)

    visited = visited or set()

    if state in visited:
        return state

    visited.add(state)

    if state is EOF:
        return EOF

    state_copy = copy.copy(state)

    state_copy.out = [
        _dup(s, visited)
        for s in state_copy.out]

    return state_copy


def _combine(origin_state: Node, target_state: Node, visited: set=None) -> None:
    """
    Set all state ends to the target state

    We could keep track of node ends instead\
    of iterating all of them on every combination.\
    But it is a worthless optimization since\
    the resulting NFAs can be cached

    :param origin_state: the root of the state\
    that will point to the target
    :param target_state: the state the origin will point at
    :param visited: for caching the visited nodes\
    and breaking the cycle
    :private:
    """
    assert isinstance(origin_state, Node)
    assert isinstance(target_state, Node)

    visited = visited or set()

    if origin_state in visited:
        return

    visited.add(origin_state)

    for i, state in enumerate(origin_state.out):
        if state is EOF:
            origin_state.out[i] = target_state
        else:
            _combine(state, target_state, visited)


def nfa(nodes: Iterator[Node]) -> Node:
    """
    Converts a sequence of nodes into a NFA\
    ready to be matched against a string

    This creates the connections for every node.\
    EOF is temporarily placed on latest created state ends\
    and replaced by a connection to other node later,\
    so leaf nodes are the only nodes containing an EOF\
    in the resulting NFA

    :param nodes: an iterator of nodes\
    to be converted into a NFA
    :return: the NFA first state/node
    :private:
    """
    states = []
    nodes = tuple(nodes)  # type: Tuple[Node]

    if not nodes:
        return Node(char='', out=[EOF])

    for node in nodes:
        if isinstance(node, CharNode):
            node.out = [EOF]
            states.append(node)
            continue

        if node.char == Symbols.JOINER:
            state_b = states.pop()
            state_a = states.pop()
            _combine(state_a, state_b)
            states.append(state_a)
            continue

        if node.char == Symbols.OR:
            state_b = states.pop()
            state_a = states.pop()
            node.out = [state_a, state_b]
            states.append(node)
            continue

        if node.char == Symbols.ZERO_OR_MORE:
            state = states.pop()
            node.out = [state, EOF]
            _combine(state, node)
            states.append(node)
            continue

        if node.char == Symbols.ONE_OR_MORE:
            state = states.pop()
            node.out = [state, EOF]
            _combine(state, node)
            states.append(state)
            continue

        if node.char == Symbols.ZERO_OR_ONE:
            state = states.pop()
            node.out = [state, EOF]
            states.append(node)
            continue

        if node.char == Symbols.GROUP_START:
            state = states.pop()
            node.out = [state]
            states.append(node)
            continue

        if node.char == Symbols.GROUP_END:
            state = states.pop()
            node.out = [EOF]
            _combine(state, node)
            states.append(state)
            continue

        if node.char == Symbols.REPETITION_RANGE:
            assert isinstance(node, RepetitionRangeNode)

            state = states.pop()
            first = None

            if node.start > 0:
                first = _dup(state)
                curr = first

                for _ in range(node.start - 1):
                    new_state = _dup(state)
                    _combine(curr, new_state)
                    curr = new_state

            # a{0} ->
            # a{0,0} ->
            # a{2} -> aa
            # a{2,2} -> aa
            if node.start == node.end:
                # todo: SkipNode
                states.append(first or Node(char='', out=[EOF]))
                continue

            # a{1,} -> aa*
            # a{,} -> a*
            if node.end is None:
                new_state = _dup(state)
                zero_or_more = OpNode(
                    char=Symbols.ZERO_OR_MORE,
                    out=[new_state, EOF])
                _combine(new_state, zero_or_more)

                if first:
                    _combine(first, zero_or_more)

                states.append(first or zero_or_more)
                continue

            # a{1,2} -> aa?
            # a{,2} -> a?a?
            if node.end is not None:
                assert node.start < node.end

                zero_or_one = OpNode(
                    char=Symbols.ZERO_OR_ONE,
                    out=[_dup(state), EOF])
                curr = zero_or_one

                for _ in range(node.start, node.end - 1):
                    zero_or_one_ = OpNode(
                        char=Symbols.ZERO_OR_ONE,
                        out=[_dup(state), EOF])
                    _combine(curr, zero_or_one_)
                    curr = zero_or_one_

                if first:
                    _combine(first, zero_or_one)

                states.append(first or zero_or_one)
                continue

            assert False, 'Bad op: %s' % repr(node)

        assert False, 'Unhandled node: %s' % repr(node)

    assert len(states) == 1

    return states[0]
