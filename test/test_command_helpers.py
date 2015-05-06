from io import StringIO
import logging
import os
import sys
import tempfile

from flexmock import flexmock
import pytest

from devassistant.command_helpers import ClHelper, CliDialogHelper
from devassistant.exceptions import ClException

from test.logger import LoggingHandler

class TestClHelper(object):
    def setup_method(self, method):
        self.tlh = LoggingHandler.create_fresh_handler()

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

    def test_run_command_cd(self):
        cwd = os.getcwd()
        try:
            # On OSX, /etc is a link to /private/etc, hence the realpath call
            tmpdir = os.path.realpath(tempfile.gettempdir())
            out = ClHelper.run_command('cd {0}'.format(tmpdir))
            assert out == ''
            assert os.getcwd() == tmpdir
        finally:
            os.chdir(cwd)

    @pytest.mark.parametrize(('correct', 'wrong', 'system_exe'), [
        ('bash', '/usr/libexec/da_auth', False),
        ('/usr/libexec/da_auth', 'bash', True),
    ])
    # TODO: remove
    # Skipping tests in Python 3.4 due to https://github.com/has207/flexmock/pull/100
    @pytest.mark.skipif(sys.version_info[:2] == (3, 4), reason='Skipped due to flexmock bug in Python 3.4')
    def test_format_as_another_user_picks_the_right_exe(self, correct, wrong, system_exe):
        flexmock(os.path).should_receive('isfile').with_args('/usr/libexec/da_auth').and_return(system_exe)
        flexmock(os).should_receive('access').with_args('/usr/libexec/da_auth', 1).and_return(system_exe)

        assert correct in ClHelper.format_for_another_user('foo', 'root')
        assert wrong not in ClHelper.format_for_another_user('foo', 'root')

    def test_log_secret(self):
        ClHelper.run_command('id', log_level=logging.INFO, log_secret=True)
        assert len(self.tlh.msgs)
        assert ('INFO', 'LOGGING PREVENTED FOR SECURITY REASONS') in self.tlh.msgs
        assert ('DEBUG', '0') in self.tlh.msgs


class TestCliDialogHelper(object):
    def setup_method(self, method):
        self.tlh = LoggingHandler()
        self.oldinp = CliDialogHelper.inp

    def teardown_method(self, method):
        sys.stdin = sys.__stdin__
        CliDialogHelper.inp = self.oldinp

    def eofraiser(self):
        raise EOFError

    @pytest.mark.parametrize((u'choice', u'expected'),[(u'y', True), (u'n', False),
                             (u'yes', True), (u'no', False), (u'Yes', True),
                             (u'No', False), (u'yEs', True), (u'nO', False)])
    def test_ask_confirm_with_message_result(self, choice, expected):
        sys.stdin = StringIO(choice)
        assert CliDialogHelper.ask_for_confirm_with_message('foo', 'bar') is expected

    def test_ask_confirm_with_message_output(self, capsys):
        sys.stdin = StringIO(u'y')
        CliDialogHelper.ask_for_confirm_with_message('foo', 'bar')
        stdout, stderr = capsys.readouterr()
        assert 'foo' in stdout
        assert 'bar' in stdout

    def test_ask_confirm_with_message_wrong_output(self, capsys):
        sys.stdin = StringIO(u'foo\nyes')
        assert CliDialogHelper.ask_for_confirm_with_message('bar', 'baz') is True
        assert 'You have to choose' in capsys.readouterr()[0] #stdout

    def test_ask_confirm_eof_error(self):
        CliDialogHelper.inp = self.eofraiser
        assert CliDialogHelper.ask_for_confirm_with_message('bar', 'baz') is None


    @pytest.mark.parametrize((u'choice', u'expected'),[(u'y', True), (u'n', False),
                             (u'yes', True), (u'no', False), (u'Yes', True),
                             (u'No', False), (u'yEs', True), (u'nO', False)])
    def test_ask_for_package_list_confirm_correct(self, choice, expected):
        sys.stdin = StringIO(choice)
        assert CliDialogHelper.ask_for_package_list_confirm(u'foo', [u'bar']) is expected

    def test_ask_for_package_list_confirm_list(self, capsys):
        sys.stdin = StringIO(u's\ny')
        CliDialogHelper.ask_for_package_list_confirm(u'foo', [u'bar'])
        stdout, stderr = capsys.readouterr()
        assert u'bar' in stdout

    def test_ask_for_package_list_confirm_eof_error(self):
        CliDialogHelper.inp = self.eofraiser
        assert CliDialogHelper.ask_for_package_list_confirm('asd', ['sdf']) is None

    @pytest.mark.parametrize(('inp', 'prompt', 'message', 'expected'), [
        (u'foo', u'bar', u'baz', u'foo'),
        (u'', u'baz', None, u''),
        ])
    def test_ask_for_user_input(self, inp, prompt, message, expected, capsys):
        sys.stdin = StringIO(inp)
        options = {}
        if message:
            options['message'] = message
        result = CliDialogHelper.ask_for_input_with_prompt(prompt, **options)
        stdout, stderr = capsys.readouterr()
        assert prompt in stdout
        if message:
            assert message in stdout
        assert result == expected

    def test_env(self):
        out = ClHelper.run_command('echo $DEVASSISTANTTESTFOO', env={'DEVASSISTANTTESTFOO': 'foo'})
        assert out == 'foo'
        # if the variable is not specified, check that there's nothing printed
        out = ClHelper.run_command('echo $DEVASSISTANTTESTFOO')
        assert out == ''
