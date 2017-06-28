# -*- coding: utf-8 -*-


class Node:

    def __init__(self, char, out=()):
        self.char = char
        self.out = out

    def __repr__(self):
        return repr((self.char, self.out))


class CharNode(Node):

    def __init__(self, is_captured=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_captured = is_captured


class SymbolNode(Node):
    """"""


class OpNode(SymbolNode):
    """"""


class GroupNode(SymbolNode):

    def __init__(
            self,
            index=None,
            is_repeated=False,
            *args,
            **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index
        self.is_repeated = is_repeated


class ShorthandNode(CharNode):
    """"""


class CharMatcher:

    def __init__(self, char, compare):
        self.char = '\\%s' % char
        self.compare = compare

    def __eq__(self, other):
        return self.compare(other)

    def __repr__(self):
        return self.char


class AlphaNumNode(ShorthandNode):
    """"""
    def __init__(self, char, *args, **kwargs):
        super().__init__(
            char=CharMatcher(char=char, compare=lambda c: c.isalnum()),
            *args,
            **kwargs)


class DigitNode(ShorthandNode):
    """"""
    def __init__(self, char, *args, **kwargs):
        super().__init__(
            char=CharMatcher(char=char, compare=lambda c: c.isdigit()),
            *args,
            **kwargs)


class EOFNode(Node):
    """"""


EOF = EOFNode(out=[], char='EOF')

