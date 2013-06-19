import pytest

from devassistant.command_helpers import ClHelper

class TestClHelper(object):
    def test_format_for_scls_no_scls(self):
        assert ClHelper.format_for_scls('foo', []) == 'foo'

    def test_format_for_scls_some_scls(self):
        scls = ['enable', 'scl1', 'scl2']
        cmd = 'foo bar'
        expected = 'scl enable scl1 scl2 - << DA_SCL_EOF\n foo bar \nDA_SCL_EOF'
        assert ClHelper.format_for_scls(cmd, scls) == expected

    def test_format_for_scls_leaves_cd_untouched(self):
        assert ClHelper.format_for_scls('cd foo', ['bar', 'baz']) == 'cd foo'
