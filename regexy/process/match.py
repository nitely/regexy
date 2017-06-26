# -*- coding: utf-8 -*-

from ..shared import (
    EOF,
    CharNode,
    GroupNode,
    exceptions)
from . import captures


__all__ = ['match']


def _get_match(states):
    for s, captured in states:
        if s == EOF:
            return captured

    raise exceptions.MatchError('No match')


def _next_states(state, captured):
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


def next_states(state, captured):
    for s in state.out:
        yield from _next_states(s, captured)


def curr_states(state, captured):
    return _next_states(state, captured)


def match(nfa, text):
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
