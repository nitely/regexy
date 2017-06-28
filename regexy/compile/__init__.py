# -*- coding: utf-8 -*-

from . import compile

__doc__ = compile.__doc__
__all__ = [
    'to_nfa',
    'to_rpn',
    'to_atoms']

to_nfa = compile.to_nfa
to_rpn = compile.to_rpn
to_atoms = compile.to_atoms
