# -*- coding: utf-8 -*-

"""
This module contains all\
the node types of the NFA

:ivar Node EOF: EOFNode singleton
:private:
"""

import unicodedata
from typing import (
    Sequence,
    Callable,
    Iterator,
    Tuple)

__all__ = [
    'Node',
    'CharNode',
    'SymbolNode',
    'OpNode',
    'GroupNode',
    'EOF',
    'SetNode',
    'ShorthandNode',
    'AlphaNumNode',
    'DigitNode',
    'StartNode',
    'EndNode']


class Node:
    """
    Base node meant to be extended

    :ivar char: character/s
    :ivar out: refs to next nodes
    :private:
    """
    def __init__(self, *, char: str, out: Sequence['Node']=()) -> None:
        self.char = char
        self.out = out

    def __repr__(self) -> str:
        return repr((self.char, self.out))


class CharNode(Node):
    """
    A node that is meant to be matched\
    against regular text characters

    :ivar is_captured: set this node for capturing
    :private:
    """
    def __init__(self, *, is_captured: bool=False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.is_captured = is_captured


class SymbolNode(Node):
    """
    Base node for symbols

    :private:
    """


class OpNode(SymbolNode):
    """
    A node for operators

    :private:
    """
    def __init__(self, *, is_greedy: bool=False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.is_greedy = is_greedy


class GroupNode(SymbolNode):
    """
    A node for capturing groups (start/end)

    :ivar index: group index
    :ivar is_repeated: denotes whether the capture\
    has repetition or not
    :private:
    """
    def __init__(
            self,
            *,
            index: int=None,
            is_repeated: bool=False,
            is_capturing: bool=True,
            name: str='',
            **kwargs) -> None:
        super().__init__(**kwargs)
        self.index = index
        self.is_repeated = is_repeated
        self.is_capturing = is_capturing
        self.name = name


class AssertionNode(SymbolNode):

    def match(self, char, next_char) -> bool:
        raise NotImplementedError


class StartNode(AssertionNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        if char == 'A':
            char = '\\%s' % char

        super().__init__(char=char, **kwargs)

    def match(self, char, next_char):
        return not char


class EndNode(AssertionNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        if char == 'z':
            char = '\\%s' % char

        super().__init__(char=char, **kwargs)

    def match(self, char, next_char):
        return not next_char


class WordBoundaryNode(AssertionNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        super().__init__(
            char='\\%s' % char,
            **kwargs)

    def match(self, char, next_char):
        is_char_w = char.isalnum()
        is_next_char_w = next_char.isalnum()
        return (
            (not char and is_next_char_w) or
            (is_char_w and not next_char) or
            (is_char_w and not is_next_char_w) or
            (not is_char_w and is_next_char_w))


class NotWordBoundaryNode(AssertionNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        super().__init__(
            char='\\%s' % char,
            **kwargs)

    def match(self, char, next_char):
        is_char_w = char.isalnum()
        is_next_char_w = next_char.isalnum()
        return not (
            (not char and is_next_char_w) or
            (is_char_w and not next_char) or
            (is_char_w and not is_next_char_w) or
            (not is_char_w and is_next_char_w))


class LookaheadNode(AssertionNode):

    def __init__(self, *, node, **kwargs) -> None:
        super().__init__(char='?=%s' % node, **kwargs)
        self._node = node

    def match(self, char, next_char):
        return next_char == self._node.char


class NotLookaheadNode(AssertionNode):

    def __init__(self, *, node, **kwargs) -> None:
        super().__init__(char='?!%s' % node, **kwargs)
        self._node = node

    def match(self, char, next_char):
        return next_char != self._node.char


class RepetitionRangeNode(OpNode):

    # todo: char should print as {start, end}

    def __init__(self, *, start: int, end: int=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.start = start
        self.end = end


class ShorthandNode(CharNode):
    """"""


class CharMatcher:

    def __init__(self, *, char: str, compare: Callable[[str], bool]) -> None:
        self.char = '\\%s' % char
        self.compare = compare

    def __eq__(self, other: str) -> bool:
        return self.compare(other)

    def __repr__(self) -> str:
        return self.char


class AlphaNumNode(ShorthandNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        super().__init__(
            char=CharMatcher(char=char, compare=lambda c: c.isalnum()),
            **kwargs)


class DigitNode(ShorthandNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        super().__init__(
            char=CharMatcher(char=char, compare=lambda c: c.isdigit()),
            **kwargs)


# Whitespace characters according to python re
WHITE_SPACES = frozenset(' \t\n\r\f\v')


class WhiteSpaceNode(ShorthandNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        super().__init__(
            char=CharMatcher(
                char=char,
                compare=lambda c: (
                    c in WHITE_SPACES or
                    unicodedata.category(c)[0] == 'Z')),
            **kwargs)


class NotWhiteSpaceNode(ShorthandNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        super().__init__(
            char=CharMatcher(
                char=char,
                compare=lambda c: (
                    c not in WHITE_SPACES and
                    unicodedata.category(c)[0] != 'Z')),
            **kwargs)


class NotAlphaNumNode(ShorthandNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        super().__init__(
            char=CharMatcher(char=char, compare=lambda c: not c.isalnum()),
            **kwargs)


class NotDigitNode(ShorthandNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        super().__init__(
            char=CharMatcher(char=char, compare=lambda c: not c.isdigit()),
            **kwargs)


class AnyNode(CharNode):

    def __init__(self, *, char: str, **kwargs) -> None:
        super().__init__(
            char=CharMatcher(char=char, compare=lambda c: c != '\n'),
            **kwargs)


class SetMatcher:

    def __init__(
            self,
            *,
            chars: Iterator[str],
            ranges: Iterator[Tuple[str, str]],
            shorthands: Iterator[CharMatcher]) -> None:
        self._chars = frozenset(chars)
        self._ranges = tuple(ranges)  # todo: interval tree
        self._shorthands = tuple(shorthands)

    def __eq__(self, other: str) -> bool:
        return (
            other in self._chars or
            any(start <= other <= end
                for start, end in self._ranges) or
            other in self._shorthands)

    def __repr__(self) -> str:
        return '[%s%s%s]' % (
            ''.join(sorted(self._chars)),
            ''.join(
                '-'.join((start, end))
                for start, end in self._ranges),
            ''.join(
                str(shorthand)
                for shorthand in self._shorthands))


class SetNode(CharNode):

    def __init__(
            self,
            *,
            chars: Iterator[str],
            ranges: Iterator[Tuple[str, str]],
            shorthands: Iterator[CharMatcher],
            **kwargs) -> None:
        super().__init__(
            char=SetMatcher(
                chars=chars,
                ranges=ranges,
                shorthands=shorthands),
            **kwargs)


class NotSetMatcher:

    def __init__(self, **kwargs) -> None:
        self._matcher = SetMatcher(**kwargs)

    def __eq__(self, other: str) -> bool:
        return other != self._matcher

    def __repr__(self) -> str:
        return '[^%s]' % repr(self._matcher)[1:-1]


class NotSetNode(CharNode):

    def __init__(
            self,
            *,
            chars: Iterator[str],
            ranges: Iterator[Tuple[str, str]],
            shorthands: Iterator[CharMatcher],
            **kwargs) -> None:
        super().__init__(
            char=NotSetMatcher(
                chars=chars,
                ranges=ranges,
                shorthands=shorthands),
            **kwargs)


class SkipNode(Node):
    """
    A node that should be skipped.\
    Very useful when the regex\
    expression is empty

    :private:
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(char='SKIP', **kwargs)


class EOFNode(Node):
    """
    A node for End Of File.\
    This denotes the end of the NFA

    :private:
    """


EOF = EOFNode(out=[], char='EOF')

