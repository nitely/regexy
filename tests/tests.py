# -*- coding: utf-8 -*-

import unittest
import logging

import regexy
from regexy.compile import to_atoms


logging.disable(logging.CRITICAL)


def new_full_match(expression, text):
    return regexy.full_match(
        regexy.compile(expression), text)


def full_match(expression, text):
    m = new_full_match(expression, text)

    if not m:
        return None

    return m.groups()


def match(expression, text):
    return regexy.match(
        regexy.compile(expression), text)


def search(expression, text):
    return regexy.search(
        regexy.compile(expression), text)


def to_nfa_str(expression):
    return str(regexy.compile(expression).state)


class RegexyTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_new_match(self):
        self.assertIsNotNone(new_full_match('a', 'a'))
        self.assertIsNone(new_full_match('b', 'a'))

    def test_full_match(self):
        self.assertIsNotNone(full_match('', ''))
        self.assertIsNotNone(full_match('a', 'a'))
        self.assertIsNotNone(full_match('(a)b', 'ab'))
        self.assertIsNotNone(full_match('(a)*', 'aa'))
        self.assertIsNotNone(full_match('((a)*b)', 'aab'))
        self.assertIsNotNone(full_match('a(b|c)*d', 'abbbbccccd'))
        self.assertIsNotNone(full_match('((a)*(b)*)', 'abbb'))
        self.assertIsNotNone(full_match('((a(b)*)*(b)*)', 'abbb'))
        self.assertIsNotNone(full_match('a|b', 'a'))
        self.assertIsNotNone(full_match('a|b', 'b'))
        self.assertIsNone(full_match('a(b|c)*d', 'ab'))
        self.assertIsNone(full_match('b', 'a'))
        self.assertIsNone(full_match('', 'a'))

    def test_match(self):
        self.assertIsNotNone(match('', ''))
        self.assertIsNotNone(match('a', 'a'))
        self.assertIsNotNone(match('ab', 'ab'))
        self.assertIsNotNone(match('a*', 'aa'))
        self.assertIsNotNone(match('^', 'a'))
        self.assertIsNotNone(match('', 'a'))
        self.assertIsNotNone(match('a', 'ab'))
        self.assertIsNotNone(match('abc', 'abcde'))
        self.assertIsNone(match('b', 'a'))
        self.assertIsNone(match('a', 'ba'))
        self.assertIsNone(match('^$', 'a'))

        self.assertEqual(
            match('(\w+)', '123abc123').groups(), ('123abc123',))
        self.assertEqual(
            match('(.*)', '123abc123').groups(), ('123abc123',))
        self.assertEqual(
            match('(.*?)', '123abc123').groups(), (None,))

    def test_search(self):
        self.assertIsNotNone(search('', ''))
        self.assertIsNotNone(search('a', 'a'))
        self.assertIsNotNone(search('ab', 'ab'))
        self.assertIsNotNone(search('a*', 'aa'))
        self.assertIsNotNone(search('^', 'a'))
        self.assertIsNotNone(search('', 'a'))
        self.assertIsNotNone(search('a', 'ab'))
        self.assertIsNotNone(search('b', 'ab'))
        self.assertIsNotNone(search('b', 'abc'))
        self.assertIsNotNone(search('abc', 'abcde'))
        self.assertIsNotNone(search('cde', 'abcde'))
        self.assertIsNotNone(search('c', 'abcde'))
        self.assertIsNone(search('b', 'a'))
        self.assertIsNone(search('^$', 'a'))

        self.assertEqual(
            search('(abc)', '123abc123').groups(), ('abc',))
        self.assertEqual(
            search('(.*)', '123abc123').groups(), ('123abc123',))
        self.assertEqual(
            search('(\d*)', '123abc456').groups(), ('123',))
        self.assertEqual(
            search('(\d*)$', '123abc456').groups(), ('456',))
        self.assertEqual(
            search('(\d+)', 'abc123def').groups(), ('123',))

    def test_repetition_cycle(self):
        self.assertIsNotNone(full_match('a**', 'aaa'))
        self.assertIsNotNone(full_match('(a*)*', 'aaa'))
        self.assertIsNotNone(full_match('((a*|b*))*', 'aaabbbaaa'))
        self.assertIsNotNone(full_match('a*{,}', 'aaa'))

    def test_captures(self):
        self.assertEqual(full_match('(a)b', 'ab'), ('a',))
        self.assertEqual(full_match('(a)*', 'aa'), (('a', 'a'),))
        self.assertEqual(full_match('((a)*b)', 'aab'), ('aab', ('a', 'a')))
        self.assertEqual(
            full_match('a(b|c)*d', 'abbbbccccd'),
            (('b', 'b', 'b', 'b', 'c', 'c', 'c', 'c'),))
        self.assertEqual(
            full_match('((a)*(b)*)', 'abbb'),
            ('abbb', ('a',), ('b', 'b', 'b')))
        self.assertEqual(
            full_match('((a(b)*)*(b)*)', 'abbb'),
            ('abbb', ('abbb',), ('b', 'b', 'b'), None))
        self.assertEqual(full_match('(a)+', 'aa'), (('a', 'a'),))
        self.assertEqual(full_match('(ab)+', 'abab'), (('ab', 'ab'),))
        self.assertEqual(full_match('(a)?', 'a'), ('a',))
        self.assertEqual(full_match('(ab)?', 'ab'), ('ab',))
        self.assertEqual(
            full_match('(a*|b*)*', 'aaabbbaaa'),
            (('aaa', 'bbb', 'aaa'),))
        self.assertEqual(
            full_match(r'(a(b))*', 'abab'), (('ab', 'ab'), ('b', 'b')))

        # These two should match the same
        self.assertEqual(
            full_match(r'((a)*n?(asd)*)*', 'aaanasdnasd'),
            (('aaanasd', 'nasd'),('a', 'a', 'a'), ('asd', 'asd')))
        self.assertEqual(
            full_match(r'((a)*n?(asd))*', 'aaanasdnasd'),
            (('aaanasd', 'nasd'), ('a', 'a', 'a'), ('asd', 'asd')))

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
        self.assertIsNotNone(full_match('a+', 'aaaa'))
        self.assertIsNotNone(full_match('ab+', 'abb'))
        self.assertIsNotNone(full_match('aba+', 'abaa'))
        self.assertIsNone(full_match('a+', ''))
        self.assertIsNone(full_match('a+', 'b'))
        self.assertIsNone(full_match('ab+', 'aab'))

    def test_zero_or_one_op(self):
        self.assertIsNotNone(full_match('a?', 'a'))
        self.assertIsNotNone(full_match('a?', ''))
        self.assertIsNotNone(full_match('ab?', 'a'))
        self.assertIsNotNone(full_match('ab?', 'ab'))
        self.assertIsNotNone(full_match('ab?a', 'aba'))
        self.assertIsNotNone(full_match('ab?a', 'aa'))
        self.assertIsNone(full_match('a?', 'aa'))
        self.assertIsNone(full_match('a?', 'b'))
        self.assertIsNone(full_match('ab?', 'abb'))

    def test_escape(self):
        self.assertEqual(full_match(r'\(a\)', '(a)'), ())
        self.assertIsNotNone(full_match(r'a\*b', 'a*b'))
        self.assertIsNotNone(full_match(r'a\*b*', 'a*bbb'))
        self.assertIsNotNone(full_match(r'\a', 'a'))
        self.assertIsNotNone(full_match(r'\\', '\\'))
        self.assertIsNotNone(full_match(r'\\\\', '\\\\'))

    def test_alphanum_shorthand(self):
        self.assertIsNotNone(full_match(r'\w', 'a'))
        self.assertIsNotNone(full_match(r'\w*', 'abc123'))
        self.assertEqual(full_match(r'(\w)', 'a'), ('a',))

    def test_digit(self):
        self.assertIsNotNone(full_match(r'\d', '1'))
        self.assertIsNotNone(full_match(r'\d*', '123'))
        self.assertEqual(full_match(r'(\d)', '1'), ('1',))
        self.assertIsNotNone(full_match(r'\d', '۲'))  # Kharosthi numeral
        self.assertIsNone(full_match(r'\d', '⅕'))

    def test_white_space_shorthand(self):
        self.assertIsNotNone(full_match(r'\s', ' '))
        self.assertIsNotNone(full_match(r'\s*', '   '))
        self.assertIsNotNone(full_match(r'\s*', ' \t\n\r\f\v'))
        self.assertIsNotNone(full_match(r'\s', '\u2028'))  # Line separator

    def test_alphanum_not_shorthand(self):
        self.assertIsNone(full_match(r'\W', 'a'))
        self.assertIsNone(full_match(r'\W*', 'abc123'))
        self.assertIsNotNone(full_match(r'\W+', '!@#'))

    def test_not_digit(self):
        self.assertIsNone(full_match(r'\D', '1'))
        self.assertIsNone(full_match(r'\D*', '123'))
        self.assertIsNone(full_match(r'\D', '۲'))  # Kharosthi numeral
        self.assertIsNotNone(full_match(r'\D', '⅕'))
        self.assertIsNotNone(full_match(r'\D+', '!@#'))

    def test_not_white_space_shorthand(self):
        self.assertIsNotNone(full_match(r'\S*', 'asd123!@#'))
        self.assertIsNone(full_match(r'\S', ' '))
        self.assertIsNone(full_match(r'\S*', '   '))
        self.assertIsNone(full_match(r'\S', '\t'))
        self.assertIsNone(full_match(r'\S', '\n'))
        self.assertIsNone(full_match(r'\S', '\r'))
        self.assertIsNone(full_match(r'\S', '\f'))
        self.assertIsNone(full_match(r'\S', '\v'))
        self.assertIsNone(full_match(r'\S', '\u2028'))  # Line separator

    def test_set(self):
        self.assertIsNotNone(full_match(r'[a]', 'a'))
        self.assertIsNotNone(full_match(r'[abc]', 'a'))
        self.assertIsNotNone(full_match(r'[abc]', 'b'))
        self.assertIsNotNone(full_match(r'[abc]', 'c'))
        self.assertIsNone(full_match(r'[abc]', 'd'))
        self.assertIsNotNone(full_match(r'[\w]', 'a'))
        self.assertIsNotNone(full_match(r'[\w]', '1'))
        self.assertIsNotNone(full_match(r'[\d]', '1'))
        self.assertIsNotNone(full_match(r'[*]', '*'))
        self.assertIsNotNone(full_match(r'[\*]', '*'))
        self.assertIsNotNone(full_match(r'[a*]', '*'))
        self.assertIsNotNone(full_match(r'[a*]', 'a'))
        self.assertIsNotNone(full_match(r'[a-z]', 'a'))
        self.assertIsNotNone(full_match(r'[a-z]', 'f'))
        self.assertIsNotNone(full_match(r'[a-z]', 'z'))
        self.assertIsNone(full_match(r'[a-z]', 'A'))
        self.assertIsNotNone(full_match(r'[0-9]', '0'))
        self.assertIsNotNone(full_match(r'[0-9]', '5'))
        self.assertIsNotNone(full_match(r'[0-9]', '9'))
        self.assertIsNone(full_match(r'[0-9]', 'a'))
        self.assertIsNotNone(full_match(r'[()[\]{}]', '('))
        self.assertIsNotNone(full_match(r'[()[\]{}]', ')'))
        self.assertIsNotNone(full_match(r'[()[\]{}]', '}'))
        self.assertIsNotNone(full_match(r'[()[\]{}]', '{'))
        self.assertIsNotNone(full_match(r'[()[\]{}]', '['))
        self.assertIsNotNone(full_match(r'[()[\]{}]', ']'))
        self.assertIsNotNone(full_match(r'[]()[{}]', '('))
        self.assertIsNotNone(full_match(r'[]()[{}]', ')'))
        self.assertIsNotNone(full_match(r'[]()[{}]', '}'))
        self.assertIsNotNone(full_match(r'[]()[{}]', '{'))
        self.assertIsNotNone(full_match(r'[]()[{}]', '['))
        self.assertIsNotNone(full_match(r'[]()[{}]', ']'))
        self.assertIsNotNone(full_match(r'[\\]', '\\'))
        self.assertIsNotNone(full_match(r'[\\\]]', '\\'))
        self.assertIsNotNone(full_match(r'[\\\]]', ']'))
        self.assertIsNotNone(full_match(r'[0-5][0-9]', '00'))
        self.assertIsNotNone(full_match(r'[0-5][0-9]', '59'))
        self.assertIsNone(full_match(r'[0-5][0-9]', '95'))
        self.assertIsNotNone(full_match(r'[0-57-9]', '1'))
        self.assertIsNotNone(full_match(r'[0-57-9]', '8'))
        self.assertIsNone(full_match(r'[0-57-9]', '6'))
        self.assertIsNotNone(full_match(r'[0-9A-Fa-f]', '4'))
        self.assertIsNotNone(full_match(r'[0-9A-Fa-f]', 'b'))
        self.assertIsNotNone(full_match(r'[0-9A-Fa-f]', 'B'))
        self.assertIsNone(full_match(r'[0-9A-Fa-f]', '-'))
        self.assertIsNotNone(full_match(r'[a\-z]', '-'))
        self.assertIsNotNone(full_match(r'[a\-z]', 'a'))
        self.assertIsNotNone(full_match(r'[a\-z]', 'z'))
        self.assertIsNone(full_match(r'[a\-z]', 'b'))
        self.assertIsNotNone(full_match(r'[a-]', 'a'))
        self.assertIsNotNone(full_match(r'[a-]', '-'))
        self.assertIsNotNone(full_match(r'[(+*)]', '+'))
        self.assertIsNotNone(full_match(r'[(+*)]', '*'))
        self.assertIsNotNone(full_match(r'[(+*)]', '('))
        self.assertIsNotNone(full_match(r'[[-\]]', '['))
        self.assertIsNotNone(full_match(r'[[-\]]', ']'))
        self.assertIsNone(full_match(r'[[-\]]', '-'))
        self.assertIsNotNone(full_match(r'[(-\)]', '('))
        self.assertIsNotNone(full_match(r'[(-\)]', ')'))
        self.assertIsNone(full_match(r'[(-\)]', '-'))
        self.assertIsNotNone(full_match(r'[\\-\\)]', '\\'))
        self.assertIsNone(full_match(r'[\\-\\)]', '-'))
        self.assertIsNotNone(full_match(r'[-]', '-'))
        self.assertIsNotNone(full_match(r'[\-]', '-'))
        self.assertIsNotNone(full_match(r'[\-\-]', '-'))
        self.assertIsNotNone(full_match(r'[\--]', '-'))
        self.assertIsNotNone(full_match(r'[\--\-]', '-'))
        self.assertIsNotNone(full_match(r'[\---]', '-'))
        self.assertIsNotNone(full_match(r'[\--\-a-z]', 'b'))
        self.assertIsNotNone(full_match(r'[\---a-z]', 'b'))
        self.assertIsNotNone(full_match(r'[-a-z]', 'b'))
        self.assertIsNotNone(full_match(r'[-a-z]', '-'))
        self.assertIsNotNone(full_match(r'[-a]', 'a'))
        self.assertIsNotNone(full_match(r'[-a]', '-'))
        self.assertIsNotNone(full_match(r'[a-d-z]', 'b'))
        self.assertIsNotNone(full_match(r'[a-d-z]', '-'))
        self.assertIsNotNone(full_match(r'[a-d-z]', 'z'))
        self.assertIsNone(full_match(r'[a-d-z]', 'e'))
        self.assertIsNotNone(full_match(r'[]]', ']'))
        self.assertIsNotNone(full_match(r'[\]]', ']'))
        self.assertIsNone(full_match(r'[]]', '['))
        self.assertIsNone(full_match(r'[]]', ']]'))

    def test_not_set(self):
        self.assertIsNone(full_match(r'[^a]', 'a'))
        self.assertEqual(full_match(r'([^b])', 'a'), ('a',))
        self.assertEqual(full_match(r'([^b]*)', 'asd'), ('asd',))
        self.assertEqual(full_match(r'([^b]*)', 'ab'), None)
        self.assertEqual(full_match(r'([^b]*b)', 'ab'), ('ab',))
        self.assertEqual(
            full_match(r'([^\d]*)(\d*)', 'asd123'),
            ('asd', '123'))
        self.assertEqual(
            full_match(r'([asd]*)([^asd]*)', 'asd123'),
            ('asd', '123'))
        self.assertEqual(
            full_match(r'(<[^>]*>)', '<asd123!@#>'),
            ('<asd123!@#>',))
        self.assertIsNotNone(full_match(r'[^]', '^'))
        self.assertIsNotNone(full_match(r'[\^]', '^'))
        self.assertIsNotNone(full_match(r'[\^a]', 'a'))
        self.assertIsNone(full_match(r'[^^]', '^'))
        self.assertIsNotNone(full_match(r'[^^]', 'a'))
        self.assertIsNotNone(full_match(r'[^-]', 'a'))
        self.assertIsNone(full_match(r'[^-]', '-'))

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
        self.assertIsNotNone(full_match(r'a{0}', ''))
        self.assertIsNotNone(full_match(r'a{0,0}', ''))
        self.assertIsNotNone(full_match(r'a{,0}', ''))
        self.assertIsNotNone(full_match(r'a{,2}', ''))
        self.assertIsNone(full_match(r'a{0}', 'a'))
        self.assertIsNone(full_match(r'a{0,0}', 'a'))
        self.assertIsNone(full_match(r'a{,0}', 'a'))

        self.assertIsNotNone(full_match(r'a{1}', 'a'))
        self.assertIsNotNone(full_match(r'a{2}', 'aa'))
        self.assertIsNotNone(full_match(r'a{3}', 'aaa'))
        self.assertIsNone(full_match(r'a{3}', 'aaaa'))
        self.assertIsNone(full_match(r'a{1}', ''))

        self.assertIsNotNone(full_match(r'a{1,1}', 'a'))
        self.assertIsNotNone(full_match(r'a{1,2}', 'a'))
        self.assertIsNotNone(full_match(r'a{1,2}', 'aa'))
        self.assertIsNone(full_match(r'a{1,2}', 'aaa'))
        self.assertIsNone(full_match(r'a{2,4}', 'a'))

        self.assertIsNotNone(full_match(r'a{1,}', 'a'))
        self.assertIsNotNone(full_match(r'a{1,}', 'aa'))
        self.assertIsNotNone(full_match(r'a{1,}', 'aaa'))
        self.assertIsNotNone(full_match(r'a{1,}', 'a' * 10))
        self.assertIsNotNone(full_match(r'a{2,}', 'aa'))
        self.assertIsNotNone(full_match(r'a{,}', 'a'))
        self.assertIsNotNone(full_match(r'a{,}', 'aa'))
        self.assertIsNotNone(full_match(r'a{,}', 'a' * 10))
        self.assertIsNotNone(full_match(r'a{,}', ''))
        self.assertIsNotNone(full_match(r'a{0,}', 'a' * 10))
        self.assertIsNotNone(full_match(r'a{0,}', ''))
        self.assertIsNone(full_match(r'a{2,}', 'a'))

        self.assertEqual(
            full_match(r'(a){,}', 'aaa'),
            (('a', 'a', 'a'),))
        self.assertEqual(
            full_match(r'(a{,}){,}', 'aaa'),
            (('aaa',),))
        self.assertEqual(
            full_match(r'(a){5}', 'a' * 5),
            (('a', 'a', 'a', 'a', 'a'),))
        self.assertEqual(
            full_match(r'(a){1,5}', 'a'),
            (('a',),))
        self.assertEqual(
            full_match(r'(a){1,5}', 'a' * 3),
            (('a', 'a', 'a'),))
        self.assertEqual(
            full_match(r'(a){,}', ''),
            (None,))

        self.assertEqual(
            full_match(r'(a{,}){,}', 'aaa'),
            (('aaa',),))
        self.assertEqual(
            full_match(r'(a{1}){,}', 'aaa'),
            (('a', 'a', 'a'),))
        self.assertEqual(
            full_match(r'(a{2}){,}', 'aaaa'),
            (('aa', 'aa'),))
        self.assertEqual(
            full_match(r'(a{,3}){,}', 'aaaa'),
            (('aaa', 'a'),))
        self.assertEqual(
            full_match(r'(a{,3}){,}', ''),
            (None,))

        self.assertEqual(
            full_match(r'(a{1,}){,}', 'aaa'),
            (('aaa',),))
        self.assertEqual(
            full_match(r'(a{1,}){,}', ''),
            (None,))
        self.assertIsNone(
            full_match(r'(a{1,})', ''))
        self.assertEqual(
            full_match(r'(a{1,})', 'a'),
            ('a',))
        self.assertEqual(
            full_match(r'(a{1,})', 'aaa'),
            ('aaa',))

        self.assertIsNotNone(full_match('a*{,}', 'aaa'))
        self.assertIsNone(full_match('a*{0}', 'aaa'))
        self.assertIsNotNone(full_match('a*{1}', 'aaa'))

    def test_circular_repetition(self):
        self.assertIsNotNone(full_match(r'((a)*(a)*)*', 'a' * 100))

    def test_non_capturing_groups(self):
        self.assertEqual(
            full_match(r'(?:a)', 'a'), ())
        self.assertEqual(
            full_match(r'(?:aaa)', 'aaa'), ())
        self.assertEqual(
            full_match(r'(a(b))*', 'abab'), (('ab', 'ab'), ('b', 'b')))
        self.assertEqual(
            full_match(r'(?:a(b))*', 'abab'), (('b', 'b'),))
        self.assertEqual(
            full_match(r'(a(?:b))*', 'abab'), (('ab', 'ab'),))
        # self.assertIsNotNone(match(r'(\))', ')'))  # fixme

    def test_greediness(self):
        self.assertEqual(
            full_match(r'(a)*(a)*(a)*', 'aaa'),
            (('a', 'a', 'a'), None, None))
        self.assertEqual(
            full_match(r'(a)*?(a)*(a)*?', 'aaa'),
            (None, ('a', 'a', 'a'), None))
        self.assertEqual(
            full_match(r'(a)*?(a)*?(a)*', 'aaa'),
            (None, None, ('a', 'a', 'a')))
        self.assertEqual(
            full_match(r'(a)*?(a)*?(a)*?', 'aaa'),
            (None, None, ('a', 'a', 'a')))

        self.assertEqual(full_match(r'(a)?(aa?)', 'aa'), ('a', 'a'))
        self.assertEqual(full_match(r'(a)??(a)', 'aa'), ('a', 'a'))
        self.assertEqual(full_match(r'(a)??(aa?)', 'aa'), (None, 'aa'))

        self.assertEqual(
            full_match(r'(a)+(a)+(a)?', 'aaa'),
            (('a', 'a'), ('a',), None))
        self.assertEqual(
            full_match(r'(a)+?(a)+(a)?', 'aaa'),
            (('a',), ('a', 'a'), None))
        self.assertEqual(
            full_match(r'(a)+?(a)+?(a)?', 'aaa'),
            (('a',), ('a',), 'a'))

        self.assertEqual(
            full_match(r'(a){,}(a){,}(a){,}', 'aaa'),
            (('a', 'a', 'a'), None, None))
        self.assertEqual(
            full_match(r'(a){,}?(a){,}(a){,}?', 'aaa'),
            (None, ('a', 'a', 'a'), None))
        self.assertEqual(
            full_match(r'(a){,}?(a){,}?(a){,}', 'aaa'),
            (None, None, ('a', 'a', 'a')))
        self.assertEqual(
            full_match(r'(a){,}?(a){,}?(a){,}?', 'aaa'),
            (None, None, ('a', 'a', 'a')))

        self.assertEqual(
            full_match(r'(a){1,}(a){1,}(a)?', 'aaa'),
            (('a', 'a'), ('a',), None))
        self.assertEqual(
            full_match(r'(a){1,}?(a){1,}(a)?', 'aaa'),
            (('a',), ('a', 'a'), None))
        self.assertEqual(
            full_match(r'(a){1,}?(a){1,}?(a)?', 'aaa'),
            (('a',), ('a',), 'a'))

    def test_assertions(self):
        self.assertIsNotNone(search(r'^a$', 'a'))
        self.assertIsNone(search(r'^a$', 'ab'))
        self.assertEqual(
            search(r'^(a)$', 'a').groups(), ('a',))
        self.assertIsNotNone(search(r'^$', ''))

        self.assertIsNotNone(search(r'\ba\b', 'a'))
        self.assertIsNone(search(r'\ba\b', 'aa'))
        self.assertEqual(
            full_match(r'([\w ]*?)(\baa\b)', 'bbaa aa'), ('bbaa ', 'aa'))
        self.assertEqual(
            full_match(r'(\baa\b)([\w ]*)', 'aa bbaa'), ('aa', ' bbaa'))
        self.assertEqual(
            full_match(r'([\w ]*?)(\bis\b)([\w ]*?)', 'This island is great'),
            ('This island ', 'is', ' great'))

        self.assertIsNone(search(r'\Ba\B', 'a'))
        self.assertIsNone(
            search(r'([\w ]*?)(\Baa\B)', 'bbaa aa'))
        self.assertIsNone(
            search(r'([\w ]*)(\Baa\B)', 'aa bbaa'))
        self.assertEqual(
            full_match(r'([\w ]*?)(\Baa\B)([\w ]*?)', 'bbaabb'), ('bb', 'aa', 'bb'))
        self.assertEqual(
            full_match(r'([\w ]*?)(\Bis\B)([\w ]*?)', 'This is my sister'),
            ('This is my s', 'is', 'ter'))

        self.assertIsNotNone(search(r'\Aa\z', 'a'))
        self.assertIsNone(search(r'\Aa\z', 'ab'))
        self.assertEqual(
            search(r'\A(a)\z', 'a').groups(), ('a',))
        self.assertEqual(
            search(r'(\Aa\z)', 'a').groups(), ('a',))

    def test_dot_any_matcher(self):
        self.assertEqual(
            full_match(r'.', 'a'), ())
        self.assertEqual(
            full_match(r'.*', 'asd123!@#'), ())
        self.assertEqual(
            full_match(r'.*', '| (•□•) | (❍ᴥ❍ʋ)'), ())
        self.assertEqual(
            full_match(r'(.*)', 'ฅ^•ﻌ•^ฅ'), ('ฅ^•ﻌ•^ฅ',))
        self.assertEqual(
            full_match(r'.', '\t'), ())
        self.assertEqual(
            full_match(r'.', '\n'), None)

    def test_lookahead_assertion(self):
        self.assertIsNotNone(full_match(r'a(?=b)b', 'ab'))
        self.assertIsNotNone(full_match(r'a(?=\w)b', 'ab'))
        self.assertIsNotNone(full_match(r'a(?=b)bc', 'abc'))
        self.assertIsNone(full_match(r'a(?=b)c', 'abc'))

    def test_not_lookahead_assertion(self):
        self.assertIsNone(full_match(r'a(?!b)b', 'ab'))
        self.assertIsNone(full_match(r'a(?!\w)b', 'ab'))
        self.assertIsNotNone(full_match(r'a(?!b)c', 'ac'))
        self.assertIsNone(full_match(r'a(?!b).*', 'ab'))
        self.assertIsNotNone(full_match(r'a(?!b).*', 'ac'))
        self.assertEqual(full_match(r'a(?!b).*', 'ac'), ())
        self.assertEqual(full_match(r'(a(?!b).*)', 'ac'), ('ac',))
        self.assertEqual(full_match(r'(a)(?!b)(.*)', 'ac'), ('a', 'c'))

    def test_group(self):
        self.assertEqual(
            new_full_match(r'(\w*)', 'foobar').group(0),
            'foobar')
        self.assertEqual(
            new_full_match(r'(?P<foo>\w*)', 'foobar').group(0),
            'foobar')
        self.assertEqual(
            new_full_match(r'(a)(b)', 'ab').group(0), 'a')
        self.assertEqual(
            new_full_match(r'(a)(b)', 'ab').group(1), 'b')
        self.assertEqual(
            new_full_match(r'(a)(b)', 'ab').groups(), ('a', 'b'))

    def test_named_groups(self):
        self.assertEqual(
            new_full_match(r'(?P<foo>\w*)', 'foobar').group_name('foo'),
            'foobar')
        self.assertEqual(
            new_full_match(r'(?P<foo>(?P<bar>\w*))', 'foobar').group_name('foo'),
            'foobar')
        self.assertEqual(
            new_full_match(r'(?P<foo>(?P<bar>\w*))', 'foobar').group_name('bar'),
            'foobar')
        self.assertEqual(
            new_full_match(r'(?P<foo>(?P<bar>\w*))', 'foobar').named_groups(),
            {'foo': 'foobar',
             'bar': 'foobar'})
        self.assertEqual(
            new_full_match(r'(?P<foo>(?P<bar>a)*b)', 'aab').group_name('foo'),
            'aab')
        self.assertEqual(
            new_full_match(r'(?P<foo>(?P<bar>a)*b)', 'aab').group_name('bar'),
            ('a', 'a'))
        self.assertEqual(
            new_full_match(r'(?P<foo>(?P<bar>a)*b)', 'aab').named_groups(),
            {'foo': 'aab',
             'bar': ('a', 'a')})
        self.assertEqual(
            new_full_match(r'((?P<bar>a)*b)', 'aab').group_name('bar'),
            ('a', 'a'))
