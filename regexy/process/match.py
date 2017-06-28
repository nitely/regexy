# -*- coding: utf-8 -*-

"""
Matching for regular expressions

:private:
"""

from typing import (
    List,
    Tuple,
    Iterator,
    Union)

from ..shared import (
    EOF,
    CharNode,
    GroupNode,
    Node,
    exceptions)
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


def _next_states(state: Node, captured: Capture) -> Iterator[Tuple[Node, Capture]]:
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
    if state is EOF:
        return (yield EOF, captured)

    if isinstance(state, CharNode):
        if state.is_captured:
            captured = captures.capture(
                char=state.char,
                prev=captured)

        return (yield state, captured)

    if isinstance(state, GroupNode):
        captured = captures.capture(
            char=state.char,
            prev=captured,
            index=state.index,
            is_repeated=state.is_repeated)

    for s in state.out:
        yield from _next_states(s, captured)


def next_states(state: Node, captured: Capture) -> Iterator[Tuple[Node, Capture]]:
    """
    Go to next states of the given state

    :param state: current state
    :param captured: current capture
    :return: one or more states
    :private:
    """
    for s in state.out:
        yield from _next_states(s, captured)


def curr_states(state: Node, captured: Capture) -> Iterator[Tuple[Node, Capture]]:
    """
    Return a state to match.\
    This may be the current state or a following one.

    :param state: current state
    :param captured: current capture
    :return: one or more states
    """
    return _next_states(state, captured)


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
    curr_list = []
    next_list = []

    curr_list.extend(curr_states(
        state=nfa.state,
        captured=None))

    for char in text:
        if not curr_list:
            break

        for curr_state, curr_captured in curr_list:
            if char != curr_state.char:
                continue

            next_list.extend(next_states(
                state=curr_state,
                captured=curr_captured))

        curr_list, next_list = next_list, curr_list
        next_list.clear()

    try:
        captured = _get_match(curr_list)
    except exceptions.MatchError:
        return None

    return captures.matched(captured, nfa.groups_count)
