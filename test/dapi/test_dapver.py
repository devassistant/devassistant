import os
import sys
from devassistant.dapi import dapver
try:
    from functools import cmp_to_key
except ImportError:
    def cmp_to_key(mycmp):
        '''Convert a cmp= function into a key= function
        Taken from http://code.activestate.com/recipes/576653-convert-a-cmp-function-to-a-key-function/'''
        class K(object):
            def __init__(self, obj, *args):
                self.obj = obj

            def __lt__(self, other):
                return mycmp(self.obj, other.obj) < 0

            def __gt__(self, other):
                return mycmp(self.obj, other.obj) > 0

            def __eq__(self, other):
                return mycmp(self.obj, other.obj) == 0

            def __le__(self, other):
                return mycmp(self.obj, other.obj) <= 0

            def __ge__(self, other):
                return mycmp(self.obj, other.obj) >= 0

            def __ne__(self, other):
                return mycmp(self.obj, other.obj) != 0
        return K


class TestDapver(object):
    '''Tests for dap version comparison'''
    def test_comparsion(self):
        '''Test the comparison by sorting'''
        versions = ['1.0', '1.0.5', '1.1dev', '1.1a', '1.1b', '1.1', '1.1.1', '1.2']
        assert versions == sorted(versions, key=cmp_to_key(dapver.compare))
