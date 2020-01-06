# -*- coding: utf-8 -*-

"""
Matching for regular expressions

:private:
"""

import collections
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


z_transitions = None  # g_transitions
all_transitions = None


def e_removal(nfa):
    global z_transitions, all_transitions
    z_transitions = collections.defaultdict(lambda: list())
    all_transitions = set()
    def _e_closure_plus(state, prev_state, visited, capts=None):
        capts = capts or []
        if state in visited:
            return
        visited.add(state)
        if isinstance(state, GroupNode):
            capts.append(state)
        if isinstance(state, (CharNode, EOFNode)):
            if capts:
                z_transitions[prev_state, state].extend(capts)
            all_transitions.add((prev_state, state))
            yield state
            return
        for s in state.out:
            yield from _e_closure_plus(s, prev_state, visited, list(capts))
    def e_closure_plus(state):
        for s in state.out:
            yield from _e_closure_plus(s, state, set())
    def e_closure0(state):
        yield from _e_closure_plus(state, None, set())
    visited = set()
    q0 = list(e_closure0(nfa))
    queue = list(q0)
    while queue:
        q = queue.pop(0)
        Q = list(e_closure_plus(q))
        for n in Q:
            if n in visited:
                continue
            visited.add(n)
            queue.append(n)
        q.out = Q
    return q0


class OrderedFrozenSet:
    def __init__(self, x):
        self.a = []
        b = set()
        for xx in x:
            if xx in b:
                continue
            self.a.append(xx)
            b.add(xx)
        self.b = frozenset(x)

    def __iter__(self):
        return self.a.__iter__()

    def __hash__(self):
        return self.b.__hash__()

    def __eq__(self, other):
        return other.__hash__() == self.__hash__()


def _e_closure(state, visited, capt=None):
    if state in visited:
        return
    visited.add(state)
    if isinstance(state, CharNode):
        yield state
        return
    if isinstance(state, EOFNode):
        yield state
        return

    # e-transition
    for s in state.out:
        yield from _e_closure(s, visited, capt)


# Return set of all states reachable from
# the given states in zero or more e-transitions
def e_closure(states):
    result = []
    for state in states:
        for s in state.out:
            result.extend(_e_closure(s, set()))
    return OrderedFrozenSet(result)


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
    return SkipNode(out=nfa)


def dfa2(nfa):
    alphabet = create_alphabet(nfa)
    T = {}
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


class CaptNode:
    def __init__(self, parent, index, node):
        self.parent = parent
        self.index = index
        self.node = node

    def __repr__(self):
        return '(%r, %r)' % (self.parent, self.index)


def extract_submatches(capt):
    import collections
    result = collections.defaultdict(lambda: [[]])
    while capt:
        if len(result[capt.node.index][-1]) == 2:
            result[capt.node.index].append([])
        if result[capt.node.index][-1]:
            a = capt.index
            b = result[capt.node.index][-1][0]
            assert len(result[capt.node.index][-1]) == 1
            result[capt.node.index][-1] = (a, b-1)
        else:
            result[capt.node.index][-1] = (capt.index,)
        capt = capt.parent
    return dict(result)


def submatch(sub_matches, states, c, i):
    result = []
    for n, ct in sub_matches:
        for mn in states:
            if (n, mn) not in all_transitions:
                continue
            ctx = ct
            for cn in z_transitions[n, mn]:
                ctx = CaptNode(parent=ctx, index=i, node=cn)
            result.append((mn, ctx))
    return result


def matchDFA(text, dfa):
    print('all_transitions', all_transitions)
    print('z_transitions', dict(z_transitions))
    T, q = dfa
    sub_matched = [(None, None)]  # last_node, capture
    for i, c in enumerate(text):
        print('matching char', c)
        t = T[q, c]
        # XXX we need to pass the state that matched c,
        #     this is a expensive hack to make it work for now
        m_states = [s for s in q if s.char == c]
        print('matched nodes', m_states)
        sub_matched = submatch(sub_matched, m_states, c, i)
        q = t
    print('end', q)
    m_states = [s for s in q if isinstance(s, EOFNode)]
    sub_matched = submatch(sub_matched, m_states, c, i+1)
    print(sub_matched)
    print('submatch', extract_submatches(_get_match(sub_matched)))
    return (
        any(isinstance(n, EOFNode) for n in q),
        extract_submatches(_get_match(sub_matched)))
