# -*- coding: utf-8 -*-

"""
This module contains all the\
exceptions this library may raise
"""

__all__ = [
    'RegexyError',
    'MatchError']


class RegexyError(Exception):
    """
    Base exception for all custom\
    errors raised by this library

    :public:
    """


class MatchError(RegexyError):
    """
    No match found. For internal use only

    :private:
    """
