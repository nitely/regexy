# -*- coding: utf-8 -*-

"""
This module contains all\
the node types of the NFA

:ivar Node EOF: EOFNode singleton
:private:
"""

from typing import Sequence

__all__ = [
    'Node',
    'CharNode',
    'SymbolNode',
    'OpNode',
    'GroupNode',
    'EOF']


class Node:
    """
    Base node meant to be extended

    :ivar char: character/s
    :ivar out: refs to next nodes
    :private:
    """
    def __init__(self, char: str, out: Sequence['Node']=()) -> None:
        self.char = char
        self.out = out

    def __repr__(self):
        return repr((self.char, self.out))


class CharNode(Node):
    """
    A node that is meant to be matched\
    against regular text characters

    :ivar is_captured: set this node for capturing
    :private:
    """
    def __init__(self, is_captured: bool=False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
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


class GroupNode(SymbolNode):
    """
    A node for capturing groups (start/end)

    :ivar index: group index
    :ivar bool: denotes whether the capture\
    has repetition or not
    :private:
    """
    def __init__(
            self,
            index: int=None,
            is_repeated: bool=False,
            *args,
            **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index
        self.is_repeated = is_repeated


class EOFNode(Node):
    """
    A node for End Of File.\
    This denotes the end of the NFA

    :private:
    """


EOF = EOFNode(out=[], char='EOF')

