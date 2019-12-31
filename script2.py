# -*- coding: utf-8 -*-

import regexy
from regexy.process.match import dfa2, matchDFA, submatch_nfa, branch_tracking_nfa

def match(text, re):
    nfa = regexy.compile(re).state
    nfa = branch_tracking_nfa(nfa)
    return matchDFA(text, dfa2(nfa), submatch_nfa(nfa))


#print(match('aabcd', '(aa)(bc)d'))
#print(match('abc', '(ab)*c'))
#print(match('ababc', '(ab)*c'))
#print(match('ab', '((a))b'))

assert match('aabcd', '(aa)(bc)d') == (True, {1: [(2, 3)], 0: [(0, 1)]})
assert match('abc', '(ab)*c') == (True, {0: [(0, 1)]})
assert match('ababc', '(ab)*c') == (True, {0: [(2, 3), (0, 1)]})
assert match('ab', '((a))b') == (True, {0: [(0, 0)], 1: [(0, 0)]})


assert match('aabc', '((a)*b)c') == (True, {0: [(0, 2)], 1: [(1, 1), (0, 0)]})
assert match('abd', 'a(b|c)d') == (True, {0: [(1, 1)]})
# indices 1-8
assert match('abbbbccccd', 'a(b|c)*d') == (True, {0: [(8, 8), (7, 7), (6, 6), (5, 5), (4, 4), (3, 3), (2, 2), (1, 1)]})
assert match('abc', '(a*)(b*)c') == (True, {1: [(1, 1)], 0: [(0, 0)]})
assert match('abc', '(a)*(b)*c') == (True, {1: [(1, 1)], 0: [(0, 0)]})
assert match('abc', '(a)*b*c') == (True, {0: [(0, 0)]})
assert match('abbbc', '((a(b)*)*(b)*)c') == (True, {0: [(0, 3)], 1: [(0, 3)], 2: [(3, 3), (2, 2), (1, 1)]})
assert match('aac', '(a)+c') == (True, {0: [(1, 1), (0, 0)]})
assert match('ababc', '(ab)+c') == (True, {0: [(2, 3), (0, 1)]})
assert match('ac', '(a)?c') == (True, {0: [(0, 0)]})
assert match('abc', '(ab)?c') == (True, {0: [(0, 1)]})
assert match('aaabbbaaac', '(a*|b*)*c') == (True, {0: [(6, 8), (3, 5), (0, 2)]})
assert match('ababc', '(a(b))*c') == (True, {0: [(2, 3), (0, 1)], 1: [(3, 3), (1, 1)]})
assert match('aaanasdnasdx', '((a)*n?(asd)*)*x') == (True, {0: [(7, 10), (0, 6)], 2: [(8, 10), (4, 6)], 1: [(2, 2), (1, 1), (0, 0)]})
assert match('aaanasdnasdx', '((a)*n?(asd))*x') == (True, {0: [(7, 10), (0, 6)], 2: [(8, 10), (4, 6)], 1: [(2, 2), (1, 1), (0, 0)]})

assert match('abde', '((ab)c)|((ab)d)e') == (True, {2: [(0, 2)], 3: [(0, 1)]})
assert match('aaaa', '(a*)a') == (True, {0: [(0, 2)]})
assert match('aaaax', '(a*)(a*)x') == (True, {1: [(4, 3)], 0: [(0, 3)]})
assert match('aaaax', '(a*?)(a*?)x') == (True, {1: [(0, 3)], 0: [(0, -1)]})


# change Node.__repr__ to debug this
#print(repr(submatch_nfa(regexy.compile('(aa)'))))
#print(repr(submatch_nfa(regexy.compile('(a)(b)'))))
#print(repr(submatch_nfa(regexy.compile('(a)|(b)'))))
