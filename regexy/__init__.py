# -*- coding: utf-8 -*-

from .compile import to_nfa as compile
from .process import match


__all__ = [
    'compile',
    'match']

__version__ = '0.2'
