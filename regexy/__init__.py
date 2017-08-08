# -*- coding: utf-8 -*-

"""
Public API
"""

from .compile import to_nfa as compile
from .process import match, full_match, search
from .shared import exceptions


__all__ = [
    'compile',
    'match',
    'full_match',
    'search',
    'exceptions']

__version__ = '0.17'
