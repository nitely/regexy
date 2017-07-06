# -*- coding: utf-8 -*-

"""
This module contains all the regex\
symbols such as operators and capturing groups
"""


class Symbols:
    """
    Symbols that a regex and/or a NFA may contain

    :ivar str JOINER: for juxtaposition of regex atoms
    :ivar str ZERO_OR_ONE: ``?`` matches zero or one char/group
    :ivar str ZERO_OR_MORE: ``*`` matches zero or more chars/groups
    :ivar str ONE_OR_MORE: ``+`` matches one or more chars/groups
    :ivar str OR: ``|`` matches chars at either at the right or the left of it
    :ivar str GROUP_START: ``(`` group start
    :ivar str GROUP_END: ``(`` group end
    :ivar str REPETITION_RANGE: ``{n,m}`` matches from n to m char/group
    :private:
    """
    JOINER = '~'
    ZERO_OR_ONE = '?'
    ZERO_OR_MORE = '*'
    ONE_OR_MORE = '+'
    OR = '|'
    GROUP_START = '('
    GROUP_END = ')'
    REPETITION_RANGE = '{n,m}'
