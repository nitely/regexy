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
    EOFNode,
    OpNode,
    CharNode,
    GroupNode,
    Node,
    SkipNode,
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
        if isinstance(s, EOFNode):
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

    if isinstance(state, EOFNode):
        yield state, captured
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

    if isinstance(state, EOFNode):
        yield state
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


def _e_closure(state, visited, capt=None):
    if state in visited:
        return
    visited.add(state)

    if isinstance(state, GroupNode):
        print('group==========')
        print(state._id)
        capt = state
    if isinstance(state, CharNode):
        state.capt = getattr(state, 'capt', [])
        if capt:
            state.capt.append(capt)
        yield state
        return
    if isinstance(state, EOFNode):
        state.capt = getattr(state, 'capt', [])
        if capt:
            state.capt.append(capt)
        yield state
        return

    # e-transition
    for s in state.out:
        yield from _e_closure(s, visited, capt)


# Return set of all states reachable from
# the given states in zero or more e-transitions
def e_closure(states):
    result = set()
    for state in states:
        for s in state.out:
            result.update(_e_closure(s, set()))
    return frozenset(result)


# extract the alphabet from the NFA graph
def create_alphabet(nfa):
    result = set()
    visited = set()
    def _make(state):
        for s in state.out:
            if s in visited:
                continue
            visited.add(s)
            if isinstance(s, CharNode):
                result.add(s.char)
            if isinstance(s, EOFNode):
                result.add(s.char)
            _make(s)
    _make(n0(nfa))
    result = list(sorted(result))
    print('alphabet=%r' % result)
    return result


# applies the nfa’s transition function to each element of q
def delta(states, symbol):
    result = set()
    for state in states:
        #for s in state.out:
            #if s.char == symbol:
            #    result.add(s)
        if state.char == symbol:
            result.add(state)
    return result


def printq(q):
    result = []
    for qi in q:
        result.append(qi.char)
    print(result)


def n0(nfa):
    # fake start node
    return SkipNode(out=[nfa.state])


def dfa2(nfa):
    alphabet = create_alphabet(nfa)
    T = {}
    # q = e_closure({nfa.state})
    # skip e_closure for now, we dont have a initial dummy node
    #q = frozenset({nfa.state})
    q = e_closure({n0(nfa)})
    print('q0', q)
    states = [q]
    result = [q]
    i = 0
    while states:
        q = states.pop(0)
        i += 1
        for c in alphabet:
            t = e_closure(delta(q, c))
            print('q%r' % i, t, 'char', c)
            printq(t)
            T[q, c] = t
            if t not in result:
                result.append(t)
                states.append(t)
    print("Table")
    print(T)
    return T, result[0]


# Return sub-NFA of transitions and captures
def submatch_nfa(nfa):
    visited = set()
    def _submatch(node):
        nonlocal visited
        if node in visited:
            assert isinstance(node, OpNode)
            return node
        visited.add(node)
        out = []
        for n in node.out:
            out.append(_submatch(n))
        assert len(out) <= 2
        if isinstance(node, EOFNode):
            assert not out
            return node.copy()
        if isinstance(node, GroupNode):
            assert len(out) > 0
            group = node.copy()
            group.out = out
            return group
        if isinstance(node, OpNode):
            assert len(out) > 0
            op = node.copy()
            op.out = out
            return op
        assert len(out) == 1
        return out[0]
    return _submatch(nfa.state)


class CaptNode:
    def __init__(self, parent, index):
        self.parent = parent
        self.index = index


def matchDFA(text, dfa, sub_nfa):
    T, q = dfa
    for i, c in enumerate(text):
        t = T[q, c]
        if any(s.capt for s in q):
            print('capt', i, q)
        q = t
    if any(s.capt for s in q):
        print('capt', len(text), q)
    print('end', q)
    return any(isinstance(n, EOFNode) for n in q)

# print(matchDFA('aaaa', dfa2(regexy.compile('a*'))))


# Don't use this. See dfa2
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
            if isinstance(s, EOFNode):
                dfa_.next[s.char] = s
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
            row.append((st.char, isinstance(st, EOFNode) or table.index(d.next[st.char])))
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
