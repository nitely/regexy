# -*- coding: utf-8 -*-

import unittest
import logging

import regexy
from regexy.compile import to_atoms


logging.disable(logging.CRITICAL)


class ReactTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_match(self):
        self.assertIsNotNone(regexy.match(regexy.compile('a'), 'a'))
        self.assertIsNotNone(regexy.match(regexy.compile('(a)b'), 'ab'))
        self.assertIsNotNone(regexy.match(regexy.compile('(a)*'), 'aa'))
        self.assertIsNotNone(regexy.match(regexy.compile('((a)*b)'), 'aab'))
        self.assertIsNotNone(regexy.match(regexy.compile('a(b|c)*d'), 'abbbbccccd'))
        self.assertIsNotNone(regexy.match(regexy.compile('((a)*(b)*)'), 'abbb'))
        self.assertIsNotNone(regexy.match(regexy.compile('((a(b)*)*(b)*)'), 'abbb'))
        self.assertIsNotNone(regexy.match(regexy.compile('a|b'), 'a'))
        self.assertIsNotNone(regexy.match(regexy.compile('a|b'), 'b'))
        self.assertIsNone(regexy.match(regexy.compile('a(b|c)*d'), 'ab'))
        self.assertIsNone(regexy.match(regexy.compile('b'), 'a'))

    def test_captures(self):
        self.assertEqual(regexy.match(regexy.compile('(a)b'), 'ab'), ('a',))
        self.assertEqual(regexy.match(regexy.compile('(a)*'), 'aa'), (('a', 'a'),))
        self.assertEqual(regexy.match(regexy.compile('((a)*b)'), 'aab'), ('aab', ('a', 'a')))
        self.assertEqual(
            regexy.match(regexy.compile('a(b|c)*d'), 'abbbbccccd'),
            (('b', 'b', 'b', 'b', 'c', 'c', 'c', 'c'),))
        self.assertEqual(
            regexy.match(regexy.compile('((a)*(b)*)'), 'abbb'),
            ('abbb', ('a',), ('b', 'b', 'b')))
        self.assertEqual(
            regexy.match(regexy.compile('((a(b)*)*(b)*)'), 'abbb'),
            ('abbb', ('abbb',), ('b', 'b', 'b'), None))

    def test_to_atoms(self):
        self.assertEqual(to_atoms('a(b|c)*d'), 'a~(b|c)*~d')
        self.assertEqual(to_atoms('abc'), 'a~b~c')
        self.assertEqual(to_atoms('(abc|def)'), '(a~b~c|d~e~f)')
        self.assertEqual(to_atoms('(abc|def)*xyz'), '(a~b~c|d~e~f)*~x~y~z')
        self.assertEqual(to_atoms('a*b'), 'a*~b')
        self.assertEqual(to_atoms('(a)b'), '(a)~b')
        self.assertEqual(to_atoms('(a)(b)'), '(a)~(b)')
