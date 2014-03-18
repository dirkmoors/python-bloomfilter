#!/usr/bin/env python
"""
Foobar.py: Description of what foobar does.
"""

import sys

__author__ = 'Dirk Moors'
__copyright__ = 'Copyright 2014, Dirk Moors'
__version__ = "1.0.0"
__status__ = "Production"

MIN_INT = -sys.maxint-1
MAX_INT = sys.maxint

def unsigned_right_shift(val, n):
    #Python equivalent of java's unsigned right shift: >>>
    return val >> n if val >= 0 else (val+0x100000000) >> n

def enforce_int_overflow(val):
    #Enforces integer overflow as is the case on platforms like Java
    if not MIN_INT <= val <= MAX_INT:
        val = (val + (MAX_INT + 1)) % (2 * (MAX_INT + 1)) - MAX_INT - 1
    return val
