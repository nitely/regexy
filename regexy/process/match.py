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
    Node,
    AssertionNode)
from ..shared import exceptions
from ..shared.collections import StatesSet
from ..compile.compile import NFA
from . import captures
from .captures import (
    Capture,
    MatchedType)


__all__ = ['match']


class Match:

    __slots__ = (
        '_captures',
        '_named_groups')

    def __init__(self, captures: tuple, named_groups: dict):
        self._captures = captures
        self._named_groups = named_groups

    def __repr__(self):
        return '%s<%s>' % (self.__class__.__name__, self._captures)

    def group(self, index):
        return self._captures[index]

    def groups(self):
        return self._captures

    def group_name(self, name):
        return self._captures[self._named_groups[name]]

    def named_groups(self):
        return {
            name: self._captures[index]
            for name, index in self._named_groups.items()}


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


def _next_states(
        state: Node,
        captured: Capture,
        chars: Tuple[str, str],
        visited: Set[Node]) -> NextStateType:
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

    if (isinstance(state, AssertionNode) and
            not state.match(*chars)):
        return

    if (isinstance(state, GroupNode) and
            state.is_capturing):
        captured = captures.capture(
            char=state.char,
            prev=captured,
            index=state.index,
            is_repeated=state.is_repeated)

    for s in state.out:
        yield from _next_states(s, captured, chars, visited)


def next_states(
        state: Node,
        captured: Capture,
        chars: Tuple[str, str]) -> NextStateType:
    """
    Go to next states of the given state

    :param state: current state
    :param captured: current capture
    :return: one or more states
    :private:
    """
    for s in state.out:
        yield from _next_states(s, captured, chars, visited=set())


def curr_states(
        state: Node,
        captured: Capture,
        chars: Tuple[str, str]) -> NextStateType:
    """
    Return a state to match.\
    This may be the current state or a following one.

    :param state: current state
    :param captured: current capture
    :return: one or more states
    """
    return _next_states(state, captured, chars, visited=set())


def _peek(iterator, sof, eof):
    iterator = iter(iterator)
    prev = sof

    for elm in iterator:
        yield prev, elm
        prev = elm

    yield prev, eof


def match(nfa: NFA, text: Iterator[str]) -> Union[Match, None]:
    """
    Match works by going through the given text\
    and matching it to the current states\
    (one or multiple states)

    The algorithm is an extended version of Thompson's NFA

    Return the matched groups or\
    an empty sequence if the regex has no groups or\
    ``None`` if no match is found

    The iterator may not be fully consumed.

    :param nfa: a NFA
    :param text: a text to match against
    :return: match or ``None``
    """
    text_it = _peek(text, sof='', eof='')

    curr_states_set = StatesSet()
    next_states_set = StatesSet()

    curr_states_set.extend(curr_states(
        state=nfa.state,
        captured=None,
        chars=next(text_it)))

    for char, next_char in text_it:
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
                captured=captured,
                chars=(char, next_char)))

        curr_states_set, next_states_set = (
            next_states_set, curr_states_set)
        next_states_set.clear()

    try:
        captured = _get_match(curr_states_set)
    except exceptions.MatchError:
        return None

    return Match(
        captures=captures.matched(captured, nfa.groups_count),
        named_groups=nfa.named_groups)


def _dfa_states(state, visited):
    if state in visited:
        # yield state
        return

    visited.add(state)

    if state is EOF:
        yield EOF
        return

    if isinstance(state, CharNode):
        yield state
        return

    for s in state.out:
        yield from _dfa_states(s, visited)


def _nxt_dfa_states(state, *args, **kw):
    for s in state.out:
        yield from _dfa_states(s, set())


class DFA:

    def __init__(self, states=None):
        self.states = states or []
        self.next = {}

    def __str__(self):
        return str([s.char for s in self.states])


def dfa(nfa):
    states = list(_dfa_states(nfa.state, visited=set()))
    first = DFA(states)
    dfa_list = [first]
    visited = []  # ordered

    table = []

    while dfa_list:
        dfa_ = dfa_list.pop()
        if dfa_ in visited:
            continue
        visited.append(dfa_)

        for s in dfa_.states:
            if s is EOF:
                dfa_.next[s.char] = EOF
                continue

            sts = list(_nxt_dfa_states(s, visited=set()))
            assert sts

            if s.char in dfa_.next:
                dfa_list.remove(dfa_.next[s.char])
                sts = dfa_.next[s.char].states[:] + [
                    s2 for s2 in sts
                    if s2 not in dfa_.next[s.char].states]
                assert len(set(sts)) == len(sts)

            for d in visited:
                if d.states == sts:
                    dfa_n = d
                    break
            else:  # no-break
                dfa_n = DFA(sts)

            dfa_.next[s.char] = dfa_n
            dfa_list.append(dfa_n)

        table.append(dfa_)

    new_table = []
    for d in table:
        row = []
        for st in d.states:
            row.append((st.char, st is EOF or table.index(d.next[st.char])))
        new_table.append(row)
    print('table')
    for row in new_table:
        print(row)
    labels = list(sorted(set(l for row in new_table for l, i in row)))
    print(labels)
    new_table2 = []
    for row in new_table:
        row = dict(row)
        row2 = []
        for l in labels:
            row2.append(row.get(l, None))
        new_table2.append(row2)
    print(new_table2)
