import pytest

from flexmock import flexmock

from devassistant.command import Command
from devassistant.command_helpers import DialogHelper
from devassistant.command_runners import AskCommandRunner
from devassistant.exceptions import CommandException, YamlSyntaxError


class TestAskCommandRunner(object):
    # There is mocking code duplication, because (at least) with flexmock 0.9.6
    # and pytest 2.4.2, the mocking in setup_method isn't applied in test
    # methods.
    def setup_method(self, method):
        self.acr = AskCommandRunner

    def test_matches(self):
        assert self.acr.matches(Command('ask_foo', []))
        assert not self.acr.matches(Command('foo', []))

    def test_run_password(self):
        flexmock(DialogHelper)
        DialogHelper.should_receive('ask_for_password').and_return('foobar')
        comm = Command('ask_password', ['$password', {}])
        p = self.acr.run(comm)

        assert comm.kwargs['password'] == 'foobar'
        assert p[0] is True
        assert p[1] == 'foobar'

    @pytest.mark.parametrize('decision', [True, False])
    def test_run_confirm(self, decision):
        flexmock(DialogHelper)
        DialogHelper.should_receive('ask_for_confirm_with_message').and_return(decision)
        comm = Command('ask_confirm', ['$var', {}])
        p = self.acr.run(comm)

        assert comm.kwargs['var'] == decision
        assert p[0] is True
        assert p[1] == decision

    @pytest.mark.parametrize(('command', 'exception', 'exception_text'), [
        (Command('foo', None),  CommandException, 'No commands specified'),
        (Command('foo', []),    CommandException, 'No commands specified'),
        (Command('foo', {}),    CommandException, 'No commands specified'),
        (Command('foo', ''),    CommandException, 'No commands specified'),
        (Command('foo', 'bar'),   YamlSyntaxError, 'Not a proper variable name: b'),
        (Command('foo', ['bar']), YamlSyntaxError, 'Not a proper variable name: bar')])
    def test_format_args(self, command, exception, exception_text):
        with pytest.raises(exception) as excinfo:
            self.acr.format_args(command)
        assert exception_text in excinfo.value
