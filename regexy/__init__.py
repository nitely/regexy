# -*- coding: utf-8 -*-

"""
Public API
"""

from .compile import to_nfa as compile
from .shared import exceptions


__all__ = [
    'compile',
    'exceptions']

__version__ = '0.16'
