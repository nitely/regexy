# -*- coding: utf-8 -*-

from ..shared import (
    Node,
    EOF,
    CharNode,
    Symbols)


__all__ = ['nfa']


def _combine(origin_state, target_state, visited=None):
    """
    Set all state ends to the target state

    We could keep track of node ends instead\
    of iterating all of them on every combination.\
    But it is a worthless optimization since\
    NFAs are cached
    """
    assert isinstance(origin_state, Node)

    visited = visited or set()

    if origin_state in visited:
        return

    visited.add(origin_state)

    for i, state in enumerate(origin_state.out):
        if state is EOF:
            origin_state.out[i] = target_state
        else:
            _combine(state, target_state, visited)


def nfa(nodes):
    states = []

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

        raise ValueError('Unhandled node: %s' % repr(node))

    assert len(states) == 1

    return states[0]
