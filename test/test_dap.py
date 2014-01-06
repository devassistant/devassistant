import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from daploader import *


class TestDap(object):
    '''Tests for the Dap class'''
    def test_no_gz(self):
        with pytest.raises(DapFileError):
            Dap('test/bz2.dap')

    def test_no_exist(self):
        with pytest.raises(DapFileError):
            Dap('foo')

    def test_no_meta(self):
        with pytest.raises(DapMetaError):
            Dap('test/no_meta.dap')
