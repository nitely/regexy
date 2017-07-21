# -*- coding: utf-8 -*-

"""
Public API
"""

from .compile import to_nfa as compile
from .process import match
from .shared import exceptions


__all__ = [
    'compile',
    'match',
    'exceptions']

__version__ = '0.8'
