# -*- coding: utf-8 -*-

"""
Tools for creating the NFA states

:private:
"""

import copy
from typing import (
    Iterator,
    Tuple)

from ..shared.nodes import (
    Node,
    EOF,
    CharNode,
    RepetitionRangeNode,
    OpNode,
    SkipNode)
from ..shared import Symbols


__all__ = ['nfa']


def _dup(state: Node, visited: set) -> Node:
    """
    Recursively shallow copy state and its connected states

    Return the copy of the given state (root)

    :param state: the root or state to copy
    :param visited: a record of states to avoid cycles
    :return: shallow copy of the root state
    :private:
    """
    assert isinstance(state, Node)

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


def dup(state: Node) -> Node:
    return _dup(state=state, visited=set())


def rep_range_fixed(node, state):
    assert node.start > 0

    first = dup(state)
    curr = first

    for _ in range(node.start - 1):
        new_state = dup(state)
        combine(curr, new_state)
        curr = new_state

    return first


def rep_range_no_end(node, state):
    assert node.end is None

    new_state = dup(state)
    zero_or_more = OpNode(
        char=Symbols.ZERO_OR_MORE,
        out=[new_state, EOF])

    if node.is_greedy:
        zero_or_more.out.reverse()

    combine(new_state, zero_or_more)
    return zero_or_more


def rep_range_with_end(node, state):
    assert node.start < node.end

    zero_or_one = OpNode(
        char=Symbols.ZERO_OR_ONE,
        out=[dup(state), EOF])

    if zero_or_one.is_greedy:
        zero_or_one.out.reverse()

    curr = zero_or_one

    for _ in range(node.start, node.end - 1):
        zero_or_one_ = OpNode(
            char=Symbols.ZERO_OR_ONE,
            out=[dup(state), EOF])

        if zero_or_one_.is_greedy:
            zero_or_one_.out.reverse()

        combine(curr, zero_or_one_)
        curr = zero_or_one_

    return zero_or_one


def _combine(origin_state: Node, target_state: Node, visited: set) -> None:
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

    if origin_state in visited:
        return

    visited.add(origin_state)

    for i, state in enumerate(origin_state.out):
        if state is EOF:
            origin_state.out[i] = target_state
        else:
            _combine(state, target_state, visited)


def combine(origin_state: Node, target_state: Node) -> None:
    _combine(origin_state, target_state, visited=set())


def nfa(nodes: Iterator[Node]) -> Node:
    """
    Converts a sequence of nodes into a NFA\
    ready to be matched against a string

    This creates the connections for every node.\
    EOF is temporarily placed on latest created state ends\
    and replaced by a connection to other node later,\
    so leaf nodes are the only nodes containing an EOF\
    in the resulting NFA

    Repetition range operators are expanded (i.e: a{1,} -> aa*)

    :param nodes: an iterator of nodes\
    to be converted into a NFA
    :return: the NFA first state/node
    :private:
    """
    states = []
    nodes = tuple(nodes)  # type: Tuple[Node]

    if not nodes:
        return SkipNode(out=[EOF])

    for node in nodes:
        if isinstance(node, CharNode):
            node.out = [EOF]
            states.append(node)
            continue

        if node.char == Symbols.JOINER:
            state_b = states.pop()
            state_a = states.pop()
            combine(state_a, state_b)
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

            if node.is_greedy:
                node.out.reverse()

            combine(state, node)
            states.append(node)
            continue

        if node.char == Symbols.ONE_OR_MORE:
            state = states.pop()
            node.out = [state, EOF]

            if node.is_greedy:
                node.out.reverse()

            combine(state, node)
            states.append(state)
            continue

        if node.char == Symbols.ZERO_OR_ONE:
            state = states.pop()
            node.out = [state, EOF]

            if node.is_greedy:
                node.out.reverse()

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
            combine(state, node)
            states.append(state)
            continue

        if node.char == Symbols.REPETITION_RANGE:
            assert isinstance(node, RepetitionRangeNode)

            state = states.pop()
            first = None

            if node.start > 0:
                first = rep_range_fixed(node, state)

            if node.start == node.end:
                states.append(first or SkipNode(out=[EOF]))
                continue

            if node.end is None:
                end = rep_range_no_end(node, state)
            else:
                end = rep_range_with_end(node, state)

            if first:
                combine(first, end)

            states.append(first or end)
            continue

        assert False, 'Unhandled node: %s' % repr(node)

    assert len(states) == 1

    return states[0]
