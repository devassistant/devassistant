import os

import pytest

from devassistant.command_helpers import ClHelper
from devassistant.exceptions import ClException

from test.logger import TestLoggingHandler

class TestClHelper(object):
    def setup_method(self, method):
        self.tlh = TestLoggingHandler()

    def test_format_for_scls_no_scls(self):
        assert ClHelper.format_for_scls('foo', []) == 'foo'

    def test_format_for_scls_some_scls(self):
        scls = ['enable', 'scl1', 'scl2']
        cmd = 'foo bar'
        expected = 'scl enable scl1 scl2 - << DA_SCL_EOF\n foo bar \nDA_SCL_EOF'
        assert ClHelper.format_for_scls(cmd, scls) == expected

    def test_format_for_scls_leaves_cd_untouched(self):
        assert ClHelper.format_for_scls('cd foo', ['bar', 'baz']) == 'cd foo'

    def test_output_from_process_with_closed_stdout(self):
        """Previously, DevAssistant occasionally failed in Travis because of race condition in
        ClHelper.run_command. The cause of this was that on very slow machines the subprocess
        would close its output (it just finished), while proc.poll() still returned None. In such
        cases, readline() returned empty string, which was attached to the stdout (represented as
        list of output lines). Stdout was then joined with "'\n'.join(stdout)" - that resulted in
        string with bazillion newlines because of all the appended empty strings."""
        test_script = os.path.join(os.path.dirname(__file__),
                                   'fixtures',
                                   'proc_with_closed_stdout.py')
        try:
            ClHelper.run_command(test_script)
        except ClException as e:
            assert '\n\n' not in e.output
