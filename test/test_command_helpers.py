import os

from devassistant.command_helpers import ClHelper
from devassistant.exceptions import ClException

from test.logger import TestLoggingHandler

class TestClHelper(object):
    def setup_method(self, method):
        self.tlh = TestLoggingHandler()

    def test_command_processors(self):
        def foo(cmd_str):
            return 'FOO=bar && ' + cmd_str
        ClHelper.command_processors['foo'] = foo
        out = ClHelper.run_command('echo $FOO')
        ClHelper.command_processors.pop('foo')
        assert out == 'bar'

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
            assert 'script really ran' in e.output
            assert '\n\n' not in e.output

    def test_output_from_process_with_lots_of_output(self):
        """When a subprocess is fired, we use readline() while it's running and then read() the
        rest once it finishes (if there is some rest). Previously, DevAssistant didn't put a
        newline between these two, so it resulted in failures like:
        https://bugzilla.redhat.com/show_bug.cgi?id=1061207
        This attempts to test this by running "cat" on very long file, hoping that this situation
        occurs, but it may not. TODO: make this test stable under any circumstances."""
        test_file = os.path.join(os.path.dirname(__file__),
                                 'fixtures',
                                 'long_cat')
        out = ClHelper.run_command('cat {0}'.format(test_file))
        assert 'ba' not in out
