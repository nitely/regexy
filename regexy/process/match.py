# -*- coding: utf-8 -*-

"""
Matching for regular expressions

:private:
"""

from typing import (
    List,
    Tuple,
    Iterator,
    Union,
    Set)

from ..shared.nodes import (
    EOF,
    CharNode,
    GroupNode,
    Node)
from ..shared import exceptions
from ..shared.collections import StatesSet
from ..compile.compile import NFA
from . import captures
from .captures import (
    Capture,
    MatchedType)


__all__ = ['match']


def _get_match(states: List[Tuple[Node, Capture]]) -> Capture:
    """
    Find a state that ended with EOF\
    meaning it matched, otherwise raise an error

    :param states: sequence of matches
    :return: the last capture associated to the match
    :raise `exceptions.MatchError`: when no match if found
    :private:
    """
    for s, captured in states:
        if s == EOF:
            return captured

    raise exceptions.MatchError('No match')


NextStateType = Iterator[Tuple[Node, Capture]]


def _next_states(state: Node, captured: Capture, visited: Set[Node]) -> NextStateType:
    """
    Go to next CharNode or EOF state.\
    Capture matches along the way

    This will follow all state connections,\
    so it may return multiple states

    :param state: current state/node
    :param captured: current capture
    :return: one or more states for the next match
    :private:
    """
    # Break a** cycle
    if state in visited:
        return

    visited.add(state)

    if state is EOF:
        yield EOF, captured
        return

    if isinstance(state, CharNode):
        yield state, captured
        return

    if isinstance(state, GroupNode) and state.is_capturing:
        captured = captures.capture(
            char=state.char,
            prev=captured,
            index=state.index,
            is_repeated=state.is_repeated)

    for s in state.out:
        yield from _next_states(s, captured, visited)


def next_states(state: Node, captured: Capture) -> NextStateType:
    """
    Go to next states of the given state

    :param state: current state
    :param captured: current capture
    :return: one or more states
    :private:
    """
    for s in state.out:
        yield from _next_states(s, captured, set())


def curr_states(state: Node, captured: Capture) -> NextStateType:
    """
    Return a state to match.\
    This may be the current state or a following one.

    :param state: current state
    :param captured: current capture
    :return: one or more states
    """
    return _next_states(state, captured, set())


def match(nfa: NFA, text: str) -> Union[MatchedType, None]:
    """
    Match works by going through the given text\
    and matching it to the current states\
    (one or multiple states)

    The algorithm is an extended version of Thompson's NFA

    Return the matched groups or\
    an empty sequence if the regex has no groups or\
    ``None`` if no match is found

    :param nfa: a NFA
    :param text: a text to match against
    :return: match or ``None``
    """
    curr_states_set = StatesSet()
    next_states_set = StatesSet()

    curr_states_set.extend(curr_states(
        state=nfa.state,
        captured=None))

    for char in text:
        if not curr_states_set:
            break

        for curr_state, captured in curr_states_set:
            if char != curr_state.char:
                continue

            if curr_state.is_captured:
                captured = captures.capture(
                    char=char,
                    prev=captured)

            next_states_set.extend(next_states(
                state=curr_state,
                captured=captured))

        curr_states_set, next_states_set = (
            next_states_set, curr_states_set)
        next_states_set.clear()

    try:
        captured = _get_match(curr_states_set)
    except exceptions.MatchError:
        return None

    return captures.matched(captured, nfa.groups_count)
