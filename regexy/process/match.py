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
    all_transitions = collections.defaultdict(lambda: list())
    def _te_closure(state, visited, capts=()):
        if state in visited:
            return
        visited.add(state)
        if isinstance(state, GroupNode):
            capts += (state,)  # copy
        if isinstance(state, (CharNode, EOFNode)):
            yield state, capts
            return
        for s in state.out:
            yield from _te_closure(s, visited, capts)
    def te_closure(state):
        for s in state.out:
            yield from _te_closure(s, set())
    def n0(nfa):
        return SkipNode(out=[nfa])
    q0 = []
    for qb, c in te_closure(n0(nfa)):
        q0.append(qb)
        z_transitions[None, qb] = c
        all_transitions[None].append(qb)
    Qw = collections.deque(q0)
    Q = set(q0)
    while Qw:
        qa = Qw.pop()
        q = []
        for qb, c in te_closure(qa):
            q.append(qb)
            z_transitions[qa, qb] = c
            all_transitions[qa].append(qb)
            if qb not in Q:
                Q.add(qb)
                Qw.append(qb)
        qa.out = q
    return q0


# Return set of all states reachable from
# the given states
def closure(states):
    result = set()
    for state in states:
        result.update(state.out)
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
        if state.char == symbol:
            result.add(state)
    return frozenset(result)


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
    q0 = closure({n0(nfa)})
    print('q0', q0)
    Qw = collections.deque([q0])
    Q = {q0}
    i = 0
    while Qw:
        q = Qw.pop()
        i += 1
        for c in alphabet:
            t = closure(delta(q, c))
            print('q%r' % i, t, 'char', c)
            printq(t)
            T[q, c] = t
            if t not in Q:
                Q.add(t)
                Qw.appendleft(t)
    print("Table")
    print(T)
    return T, q0


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


# O(m)
def submatch(sub_matches, states, i):
    result = []
    for n, ct in sub_matches:
        for nt in all_transitions[n]:
            if nt not in states:
                continue
            ctx = ct
            for cn in z_transitions[n, nt]:
                ctx = CaptNode(parent=ctx, index=i, node=cn)
            result.append((nt, ctx))
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
        m_states = set(s for s in q if s.char == c)
        print('matched nodes', m_states)
        sub_matched = submatch(sub_matched, m_states, i)
        q = t
    print('end', q)
    m_states = [s for s in q if isinstance(s, EOFNode)]
    sub_matched = submatch(sub_matched, m_states, i+1)
    print(sub_matched)
    print('submatch', extract_submatches(_get_match(sub_matched)))
    return (
        any(isinstance(n, EOFNode) for n in q),
        extract_submatches(_get_match(sub_matched)))
