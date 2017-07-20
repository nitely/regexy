# -*- coding: utf-8 -*-

import unittest
import logging

import regexy
from regexy.compile import to_atoms


logging.disable(logging.CRITICAL)


def match(expression, text):
    return regexy.match(
        regexy.compile(expression),
        text)


def to_nfa_str(expression):
    return str(regexy.compile(expression).state)


class RegexyTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_match(self):
        self.assertIsNotNone(match('', ''))
        self.assertIsNotNone(match('a', 'a'))
        self.assertIsNotNone(match('(a)b', 'ab'))
        self.assertIsNotNone(match('(a)*', 'aa'))
        self.assertIsNotNone(match('((a)*b)', 'aab'))
        self.assertIsNotNone(match('a(b|c)*d', 'abbbbccccd'))
        self.assertIsNotNone(match('((a)*(b)*)', 'abbb'))
        self.assertIsNotNone(match('((a(b)*)*(b)*)', 'abbb'))
        self.assertIsNotNone(match('a|b', 'a'))
        self.assertIsNotNone(match('a|b', 'b'))
        self.assertIsNone(match('a(b|c)*d', 'ab'))
        self.assertIsNone(match('b', 'a'))
        self.assertIsNone(match('', 'a'))

    def test_repetition_cycle(self):
        self.assertIsNotNone(match('a**', 'aaa'))
        self.assertIsNotNone(match('(a*)*', 'aaa'))
        self.assertIsNotNone(match('((a*|b*))*', 'aaabbbaaa'))
        self.assertIsNotNone(match('a*{,}', 'aaa'))

    def test_captures(self):
        self.assertEqual(match('(a)b', 'ab'), ('a',))
        self.assertEqual(match('(a)*', 'aa'), (('a', 'a'),))
        self.assertEqual(match('((a)*b)', 'aab'), ('aab', ('a', 'a')))
        self.assertEqual(
            match('a(b|c)*d', 'abbbbccccd'),
            (('b', 'b', 'b', 'b', 'c', 'c', 'c', 'c'),))
        self.assertEqual(
            match('((a)*(b)*)', 'abbb'),
            ('abbb', ('a',), ('b', 'b', 'b')))
        self.assertEqual(
            match('((a(b)*)*(b)*)', 'abbb'),
            ('abbb', ('abbb',), ('b', 'b', 'b'), None))
        self.assertEqual(match('(a)+', 'aa'), (('a', 'a'),))
        self.assertEqual(match('(ab)+', 'abab'), (('ab', 'ab'),))
        self.assertEqual(match('(a)?', 'a'), ('a',))
        self.assertEqual(match('(ab)?', 'ab'), ('ab',))
        self.assertEqual(
            match('(a*|b*)*', 'aaabbbaaa'),
            (('aaa', 'bbb', 'aaa'),))
        self.assertEqual(
            match(r'(a(b))*', 'abab'), (('ab', 'ab'), 'bb'))  # fixme: should be (('ab', 'ab'), ('b', 'b'))

    def test_to_atoms(self):
        self.assertEqual(to_atoms('a(b|c)*d'), 'a~(b|c)*~d')
        self.assertEqual(to_atoms('abc'), 'a~b~c')
        self.assertEqual(to_atoms('(abc|def)'), '(a~b~c|d~e~f)')
        self.assertEqual(to_atoms('(abc|def)*xyz'), '(a~b~c|d~e~f)*~x~y~z')
        self.assertEqual(to_atoms('a*b'), 'a*~b')
        self.assertEqual(to_atoms('(a)b'), '(a)~b')
        self.assertEqual(to_atoms('(a)(b)'), '(a)~(b)')
        self.assertEqual(to_atoms(r'\a'), 'a')
        self.assertEqual(to_atoms(r'a\*b'), 'a~*~b')
        self.assertEqual(to_atoms(r'\(a\)'), '(~a~)')
        self.assertEqual(to_atoms(r'\w'), '\w')
        self.assertEqual(to_atoms(r'\d'), '\d')
        self.assertEqual(to_atoms(r'[a-z]'), '[a-z]')
        self.assertEqual(to_atoms(r'[a\-z]'), '[-az]')

    def test_one_or_more_op(self):
        self.assertIsNotNone(match('a+', 'aaaa'))
        self.assertIsNotNone(match('ab+', 'abb'))
        self.assertIsNotNone(match('aba+', 'abaa'))
        self.assertIsNone(match('a+', ''))
        self.assertIsNone(match('a+', 'b'))
        self.assertIsNone(match('ab+', 'aab'))

    def test_zero_or_one_op(self):
        self.assertIsNotNone(match('a?', 'a'))
        self.assertIsNotNone(match('a?', ''))
        self.assertIsNotNone(match('ab?', 'a'))
        self.assertIsNotNone(match('ab?', 'ab'))
        self.assertIsNotNone(match('ab?a', 'aba'))
        self.assertIsNotNone(match('ab?a', 'aa'))
        self.assertIsNone(match('a?', 'aa'))
        self.assertIsNone(match('a?', 'b'))
        self.assertIsNone(match('ab?', 'abb'))

    def test_escape(self):
        self.assertEqual(match(r'\(a\)', '(a)'), ())
        self.assertIsNotNone(match(r'a\*b', 'a*b'))
        self.assertIsNotNone(match(r'a\*b*', 'a*bbb'))
        self.assertIsNotNone(match(r'\a', 'a'))
        self.assertIsNotNone(match(r'\\', '\\'))
        self.assertIsNotNone(match(r'\\\\', '\\\\'))

    def test_alphanum_shorthand(self):
        self.assertIsNotNone(match(r'\w', 'a'))
        self.assertIsNotNone(match(r'\w*', 'abc123'))
        self.assertEqual(match(r'(\w)', 'a'), ('a',))

    def test_digit(self):
        self.assertIsNotNone(match(r'\d', '1'))
        self.assertIsNotNone(match(r'\d*', '123'))
        self.assertEqual(match(r'(\d)', '1'), ('1',))
        self.assertIsNotNone(match(r'\d', '۲'))  # Kharosthi numeral
        self.assertIsNone(match(r'\d', '⅕'))

    def test_set(self):
        self.assertIsNotNone(match(r'[a]', 'a'))
        self.assertIsNotNone(match(r'[abc]', 'a'))
        self.assertIsNotNone(match(r'[abc]', 'b'))
        self.assertIsNotNone(match(r'[abc]', 'c'))
        self.assertIsNone(match(r'[abc]', 'd'))
        self.assertIsNotNone(match(r'[\w]', 'a'))
        self.assertIsNotNone(match(r'[\w]', '1'))
        self.assertIsNotNone(match(r'[\d]', '1'))
        self.assertIsNotNone(match(r'[*]', '*'))
        self.assertIsNotNone(match(r'[\*]', '*'))
        self.assertIsNotNone(match(r'[a*]', '*'))
        self.assertIsNotNone(match(r'[a*]', 'a'))
        self.assertIsNotNone(match(r'[a-z]', 'a'))
        self.assertIsNotNone(match(r'[a-z]', 'f'))
        self.assertIsNotNone(match(r'[a-z]', 'z'))
        self.assertIsNone(match(r'[a-z]', 'A'))
        self.assertIsNotNone(match(r'[0-9]', '0'))
        self.assertIsNotNone(match(r'[0-9]', '5'))
        self.assertIsNotNone(match(r'[0-9]', '9'))
        self.assertIsNone(match(r'[0-9]', 'a'))
        self.assertIsNotNone(match(r'[()[\]{}]', '('))
        self.assertIsNotNone(match(r'[()[\]{}]', ')'))
        self.assertIsNotNone(match(r'[()[\]{}]', '}'))
        self.assertIsNotNone(match(r'[()[\]{}]', '{'))
        self.assertIsNotNone(match(r'[()[\]{}]', '['))
        self.assertIsNotNone(match(r'[()[\]{}]', ']'))
        self.assertIsNotNone(match(r'[]()[{}]', '('))
        self.assertIsNotNone(match(r'[]()[{}]', ')'))
        self.assertIsNotNone(match(r'[]()[{}]', '}'))
        self.assertIsNotNone(match(r'[]()[{}]', '{'))
        self.assertIsNotNone(match(r'[]()[{}]', '['))
        self.assertIsNotNone(match(r'[]()[{}]', ']'))
        self.assertIsNotNone(match(r'[\\]', '\\'))
        self.assertIsNotNone(match(r'[\\\]]', '\\'))
        self.assertIsNotNone(match(r'[\\\]]', ']'))
        self.assertIsNotNone(match(r'[0-5][0-9]', '00'))
        self.assertIsNotNone(match(r'[0-5][0-9]', '59'))
        self.assertIsNone(match(r'[0-5][0-9]', '95'))
        self.assertIsNotNone(match(r'[0-57-9]', '1'))
        self.assertIsNotNone(match(r'[0-57-9]', '8'))
        self.assertIsNone(match(r'[0-57-9]', '6'))
        self.assertIsNotNone(match(r'[0-9A-Fa-f]', '4'))
        self.assertIsNotNone(match(r'[0-9A-Fa-f]', 'b'))
        self.assertIsNotNone(match(r'[0-9A-Fa-f]', 'B'))
        self.assertIsNone(match(r'[0-9A-Fa-f]', '-'))
        self.assertIsNotNone(match(r'[a\-z]', '-'))
        self.assertIsNotNone(match(r'[a\-z]', 'a'))
        self.assertIsNotNone(match(r'[a\-z]', 'z'))
        self.assertIsNone(match(r'[a\-z]', 'b'))
        self.assertIsNotNone(match(r'[a-]', 'a'))
        self.assertIsNotNone(match(r'[a-]', '-'))
        self.assertIsNotNone(match(r'[(+*)]', '+'))
        self.assertIsNotNone(match(r'[(+*)]', '*'))
        self.assertIsNotNone(match(r'[(+*)]', '('))
        self.assertIsNotNone(match(r'[[-\]]', '['))
        self.assertIsNotNone(match(r'[[-\]]', ']'))
        self.assertIsNone(match(r'[[-\]]', '-'))
        self.assertIsNotNone(match(r'[(-\)]', '('))
        self.assertIsNotNone(match(r'[(-\)]', ')'))
        self.assertIsNone(match(r'[(-\)]', '-'))
        self.assertIsNotNone(match(r'[\\-\\)]', '\\'))
        self.assertIsNone(match(r'[\\-\\)]', '-'))
        self.assertIsNotNone(match(r'[-]', '-'))
        self.assertIsNotNone(match(r'[\-]', '-'))
        self.assertIsNotNone(match(r'[\-\-]', '-'))
        self.assertIsNotNone(match(r'[\--]', '-'))
        self.assertIsNotNone(match(r'[\--\-]', '-'))
        self.assertIsNotNone(match(r'[\---]', '-'))
        self.assertIsNotNone(match(r'[\--\-a-z]', 'b'))
        self.assertIsNotNone(match(r'[\---a-z]', 'b'))
        self.assertIsNotNone(match(r'[-a-z]', 'b'))
        self.assertIsNotNone(match(r'[-a-z]', '-'))
        self.assertIsNotNone(match(r'[-a]', 'a'))
        self.assertIsNotNone(match(r'[-a]', '-'))
        self.assertIsNotNone(match(r'[a-d-z]', 'b'))
        self.assertIsNotNone(match(r'[a-d-z]', '-'))
        self.assertIsNotNone(match(r'[a-d-z]', 'z'))
        self.assertIsNone(match(r'[a-d-z]', 'e'))
        self.assertIsNotNone(match(r'[]]', ']'))
        self.assertIsNotNone(match(r'[\]]', ']'))
        self.assertIsNone(match(r'[]]', '['))
        self.assertIsNone(match(r'[]]', ']]'))

    def test_repetition_range_expand(self):
        self.assertEqual(to_nfa_str(r'a{0}'), to_nfa_str(r''))
        self.assertEqual(to_nfa_str(r'a{1}'), to_nfa_str(r'a'))
        self.assertEqual(to_nfa_str(r'a{10}'), to_nfa_str(r'a' * 10))
        self.assertEqual(to_nfa_str(r'a{1,}'), to_nfa_str(r'aa*'))
        self.assertEqual(to_nfa_str(r'a{10,}'), to_nfa_str(r'a' * 10 + r'a*'))
        self.assertEqual(to_nfa_str(r'a{10,10}'), to_nfa_str(r'a' * 10))
        self.assertEqual(to_nfa_str(r'a{0,0}'), to_nfa_str(r''))
        self.assertEqual(to_nfa_str(r'a{1,2}'), to_nfa_str(r'aa?'))
        self.assertEqual(to_nfa_str(r'a{2,4}'), to_nfa_str(r'aaa?a?'))
        self.assertEqual(to_nfa_str(r'a{,10}'), to_nfa_str(r'a?' * 10))
        self.assertEqual(to_nfa_str(r'a{0,10}'), to_nfa_str(r'a?' * 10))
        self.assertEqual(to_nfa_str(r'a{,}'), to_nfa_str(r'a*'))

    def test_repetition_range(self):
        self.assertIsNotNone(match(r'a{0}', ''))
        self.assertIsNotNone(match(r'a{0,0}', ''))
        self.assertIsNotNone(match(r'a{,0}', ''))
        self.assertIsNotNone(match(r'a{,2}', ''))
        self.assertIsNone(match(r'a{0}', 'a'))
        self.assertIsNone(match(r'a{0,0}', 'a'))
        self.assertIsNone(match(r'a{,0}', 'a'))

        self.assertIsNotNone(match(r'a{1}', 'a'))
        self.assertIsNotNone(match(r'a{2}', 'aa'))
        self.assertIsNotNone(match(r'a{3}', 'aaa'))
        self.assertIsNone(match(r'a{3}', 'aaaa'))
        self.assertIsNone(match(r'a{1}', ''))

        self.assertIsNotNone(match(r'a{1,1}', 'a'))
        self.assertIsNotNone(match(r'a{1,2}', 'a'))
        self.assertIsNotNone(match(r'a{1,2}', 'aa'))
        self.assertIsNone(match(r'a{1,2}', 'aaa'))
        self.assertIsNone(match(r'a{2,4}', 'a'))

        self.assertIsNotNone(match(r'a{1,}', 'a'))
        self.assertIsNotNone(match(r'a{1,}', 'aa'))
        self.assertIsNotNone(match(r'a{1,}', 'aaa'))
        self.assertIsNotNone(match(r'a{1,}', 'a' * 10))
        self.assertIsNotNone(match(r'a{2,}', 'aa'))
        self.assertIsNotNone(match(r'a{,}', 'a'))
        self.assertIsNotNone(match(r'a{,}', 'aa'))
        self.assertIsNotNone(match(r'a{,}', 'a' * 10))
        self.assertIsNotNone(match(r'a{,}', ''))
        self.assertIsNotNone(match(r'a{0,}', 'a' * 10))
        self.assertIsNotNone(match(r'a{0,}', ''))
        self.assertIsNone(match(r'a{2,}', 'a'))

        self.assertEqual(
            match(r'(a){,}', 'aaa'),
            (('a', 'a', 'a'),))
        self.assertEqual(
            match(r'(a{,}){,}', 'aaa'),
            (('aaa',),))
        self.assertEqual(
            match(r'(a){5}', 'a' * 5),
            (('a', 'a', 'a', 'a', 'a'),))
        self.assertEqual(
            match(r'(a){1,5}', 'a'),
            (('a',),))
        self.assertEqual(
            match(r'(a){1,5}', 'a' * 3),
            (('a', 'a', 'a'),))
        self.assertEqual(
            match(r'(a){,}', ''),
            (None,))

        self.assertEqual(
            match(r'(a{,}){,}', 'aaa'),
            (('aaa',),))
        self.assertEqual(
            match(r'(a{1}){,}', 'aaa'),
            (('a', 'a', 'a'),))
        self.assertEqual(
            match(r'(a{2}){,}', 'aaaa'),
            (('aa', 'aa'),))
        self.assertEqual(
            match(r'(a{,3}){,}', 'aaaa'),
            (('aaa', 'a'),))
        self.assertEqual(
            match(r'(a{,3}){,}', ''),
            (None,))

        self.assertEqual(
            match(r'(a{1,}){,}', 'aaa'),
            (('aaa',),))
        self.assertEqual(
            match(r'(a{1,}){,}', ''),
            (None,))
        self.assertIsNone(
            match(r'(a{1,})', ''))
        self.assertEqual(
            match(r'(a{1,})', 'a'),
            ('a',))
        self.assertEqual(
            match(r'(a{1,})', 'aaa'),
            ('aaa',))

        self.assertIsNotNone(match('a*{,}', 'aaa'))
        self.assertIsNone(match('a*{0}', 'aaa'))
        self.assertIsNotNone(match('a*{1}', 'aaa'))

    def test_circular_repetition(self):
        self.assertIsNotNone(match(r'((a)*(a)*)*', 'a' * 100))

    def test_non_capturing_groups(self):
        self.assertEqual(
            match(r'(?:a)', 'a'), ())
        self.assertEqual(
            match(r'(?:aaa)', 'aaa'), ())
        # (a(b))* -> ((ab, ab), (b, b))
        # (?:a(b))* -> ((b, b), )
        # (a(?:b))* -> ((ab, ab), )
        # (a(b(c)))* -> ((abc, abc), (bc, bc), (c, c))
        # (a(b)*)* -> ((abb, abb), ((b, b), (b, b)))
        # (a(b(c)*)*)* -> ((abbcc, abbcc), ((b, bcc), (b, bcc)), ((None, (c, c)), (None, (c, c))))
        self.assertEqual(
            match(r'(a(b))*', 'abab'), (('ab', 'ab'), 'bb'))  # fixme
        self.assertEqual(
            match(r'(?:a(b))*', 'abab'), ('bb',))  # fixme ^
        self.assertEqual(
            match(r'(a(?:b))*', 'abab'), (('ab', 'ab'), ))
        # self.assertIsNotNone(match(r'(\))', ')'))  # fixme

        # self.assertIsNone(match(r'((a)*n?(asd))*', 'aaanasdnasd'))  # fixme
        # should be equal to r'((a)*n?(asd)*)*' (see last capture)

    def test_greediness(self):
        self.assertEqual(
            match(r'(a)*(a)*(a)*', 'aaa'),
            (('a', 'a', 'a'), None, None))
        self.assertEqual(
            match(r'(a)*?(a)*(a)*?', 'aaa'),
            (None, ('a', 'a', 'a'), None))
        self.assertEqual(
            match(r'(a)*?(a)*?(a)*', 'aaa'),
            (None, None, ('a', 'a', 'a')))
        self.assertEqual(
            match(r'(a)*?(a)*?(a)*?', 'aaa'),
            (None, None, ('a', 'a', 'a')))

        self.assertEqual(match(r'(a)?(aa?)', 'aa'), ('a', 'a'))
        self.assertEqual(match(r'(a)??(a)', 'aa'), ('a', 'a'))
        self.assertEqual(match(r'(a)??(aa?)', 'aa'), (None, 'aa'))

        self.assertEqual(
            match(r'(a)+(a)+(a)?', 'aaa'),
            (('a', 'a'), ('a',), None))
        self.assertEqual(
            match(r'(a)+?(a)+(a)?', 'aaa'),
            (('a',), ('a', 'a'), None))
        self.assertEqual(
            match(r'(a)+?(a)+?(a)?', 'aaa'),
            (('a',), ('a',), 'a'))

        self.assertEqual(
            match(r'(a){,}(a){,}(a){,}', 'aaa'),
            (('a', 'a', 'a'), None, None))
        self.assertEqual(
            match(r'(a){,}?(a){,}(a){,}?', 'aaa'),
            (None, ('a', 'a', 'a'), None))
        self.assertEqual(
            match(r'(a){,}?(a){,}?(a){,}', 'aaa'),
            (None, None, ('a', 'a', 'a')))
        self.assertEqual(
            match(r'(a){,}?(a){,}?(a){,}?', 'aaa'),
            (None, None, ('a', 'a', 'a')))

        self.assertEqual(
            match(r'(a){1,}(a){1,}(a)?', 'aaa'),
            (('a', 'a'), ('a',), None))
        self.assertEqual(
            match(r'(a){1,}?(a){1,}(a)?', 'aaa'),
            (('a',), ('a', 'a'), None))
        self.assertEqual(
            match(r'(a){1,}?(a){1,}?(a)?', 'aaa'),
            (('a',), ('a',), 'a'))
