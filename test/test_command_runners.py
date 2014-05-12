import os

import pytest
from flexmock import flexmock

from devassistant.assistant_base import AssistantBase
from devassistant.command_helpers import DialogHelper
from devassistant.command_runners import AskCommandRunner, ClCommandRunner, \
    Jinja2Runner, LogCommandRunner, NormalizeCommandRunner, UseCommandRunner
from devassistant.exceptions import CommandException, RunException
from devassistant.lang import Command
from devassistant.yaml_assistant import YamlAssistant

from test.logger import TestLoggingHandler

class CreatorAssistant(AssistantBase):
    name = 'crt'

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
        comm = Command('ask_password', {})
        res = self.acr.run(comm)

        assert res[0] is True
        assert res[1] == 'foobar'

    @pytest.mark.parametrize('decision', [True, False])
    def test_run_confirm(self, decision):
        flexmock(DialogHelper)
        DialogHelper.should_receive('ask_for_confirm_with_message').and_return(decision)
        comm = Command('ask_confirm', {})
        res = self.acr.run(comm)

        assert res[0] is decision
        assert res[1] == decision


class TestUseCommandRunner(object):
    def setup_class(self):
        parent = YamlAssistant('parent', {}, '', CreatorAssistant())
        setattr(parent, '_foo', 'bar')
        mid = YamlAssistant('mid', {}, '', parent)
        setattr(mid, '_bar', 'baz')
        leaf = YamlAssistant('leaf', {}, '', mid)

        self.ass = {'parent': parent, 'mid': mid, 'leaf': leaf}

    def setup_method(self, method):
        self.ccr = UseCommandRunner

    def test_matches(self):
        assert self.ccr.matches(Command('use', None))
        assert not self.ccr.matches(Command('foo', None))

    @pytest.mark.parametrize(('command', 'result'), [
                             ('self.run', False),
                             ('self.foo.bar', False),
                             ('super.run', False),
                             ('super.foo.bar.baz', False),
                             ('foo.run', True),
                             ('bar.baz.dependencies', True)])
    def test_is_snippet_call(self, command, result):
        assert self.ccr.is_snippet_call(command) is result
        assert self.ccr.is_snippet_call('{cmd}.foo'.format(cmd=command)) is result


    @pytest.mark.parametrize('snip', ['snippet1', 'snippet2'])
    def test_get_snippet(self, snip):
        assert self.ccr.get_snippet(snip).name == snip

    def test_get_snippet_fails(self):
        with pytest.raises(CommandException):
            self.ccr.get_snippet('foo.bar.baz')

    @pytest.mark.parametrize(('section_name', 'snip_name'), [
                             ('args', 'snippet1'),
                             ('run', 'snippet1'),
                             ('run', 'snippet2')])
    def test_get_snippet_section(self, section_name, snip_name):
        snip = self.ccr.get_snippet(snip_name)
        assert self.ccr.get_snippet_section(section_name, snip) is not None

    def test_get_snippet_section_fails(self):
        snip = self.ccr.get_snippet('snippet1')
        with pytest.raises(CommandException):
            self.ccr.get_snippet_section('foo', snip)

    @pytest.mark.parametrize(('assistant', 'section', 'origin', 'expected'), [
                             ('self', 'foo', 'parent', 'parent'),
                             ('self', 'foo', 'leaf', 'leaf'),
                             ('super', 'foo', 'leaf', 'parent'),
                             ('super', 'bar', 'leaf', 'mid')
                             ])
    def test_get_assistant(self, assistant, section, origin, expected):
        assert self.ccr.get_assistant(assistant, section, self.ass[origin]) == self.ass[expected]


class TestClCommandRunner(object):
    def setup_method(self, method):
        self.cl = ClCommandRunner
        self.tlh = TestLoggingHandler.create_fresh_handler()

    def test_command_passes(self):
        self.cl.run(Command('cl', 'true'))

    def test_command_fails(self):
        with pytest.raises(RunException):
            self.cl.run(Command('cl', 'false'))

    def test_run_logs_command_at_debug(self):
        # previously, this test used 'ls', but that is in different locations on different
        # distributions (due to Fedora's usrmove), so use something that should be common
        self.cl.run(Command('cl', 'id'))
        assert ('DEBUG', 'id') in self.tlh.msgs

    def test_run_logs_command_at_info_if_asked(self):
        self.cl.run(Command('cl_i', 'id'))
        assert ('INFO', 'id') in self.tlh.msgs


class TestDependenciesCommandRunner(object):
    pass


class TestDotDevassistantCommandRunner(object):
    pass


class TestGitHubCommandRunner(object):
    pass


class TestJinja2CommandRunner(object):
    def setup_method(self, method):
        self.jr = Jinja2Runner
        self.filesdir = os.path.join(os.path.dirname(__file__), 'fixtures', 'files')

    def is_file_exists(self, tmpdir, f):
        return os.path.isfile(os.path.join(tmpdir.strpath, f))

    def make_sure_file_does_not_exists(self, tmpdir, f):
        fn = os.path.join(tmpdir.strpath, f)
        if (os.path.exists(fn)):
            os.remove(fn)

    def get_file_contents(self, tmpdir, f):
        return open(os.path.join(tmpdir.strpath, f)).read()

    def test_matches(self):
        assert self.jr.matches(Command('jinja_render', None))

    def test_render_tpl_file_default_case_1(self, tmpdir):
        fn = 'jinja_template.py'
        # Case 1: template name ends w/ '.tpl'
        fntpl = fn + '.tpl'
        self.make_sure_file_does_not_exists(tmpdir, fn)
        inp = {'template': {'source': fntpl},
               'data': {'what': 'foo'},
               'destination': tmpdir.strpath}
        c = Command('jinja_render',
                    inp,
                    kwargs={'__files_dir__': [self.filesdir]})
        c.run()
        assert self.is_file_exists(tmpdir, fn) and self.get_file_contents(tmpdir, fn) == 'print("foo")'

    def test_render_tpl_file_default_case_2(self, tmpdir):
        fn = 'jinja_template.py'
        # Case 2: output filename will be the same!
        fntpl = fn
        self.make_sure_file_does_not_exists(tmpdir, fn)
        inp = {'template': {'source': fntpl},
               'data': {'what': 'foo'},
               'destination': tmpdir.strpath}
        c = Command('jinja_render',
                    inp,
                    kwargs={'__files_dir__': [self.filesdir]})
        c.run()
        assert self.is_file_exists(tmpdir, fn) and self.get_file_contents(tmpdir, fn) == 'print("foo")'

    def test_render_tpl_file_set_output_case(self, tmpdir):
        # Case 3: set desired output name explicitly
        fn ='rendered_jinja_template.py'
        fntpl = 'jinja_template.py.tpl'
        self.make_sure_file_does_not_exists(tmpdir, fn)
        inp = {'template': {'source': fntpl},
               'data': {'what': 'foo'},
               'output': fn,
               'destination': tmpdir.strpath}
        c = Command('jinja_render',
                    inp,
                    kwargs={'__files_dir__': [self.filesdir]})
        c.run()
        assert self.is_file_exists(tmpdir, fn) and self.get_file_contents(tmpdir, fn) == 'print("foo")'

    def test_render_with_tpl_in_file_subdir(self, tmpdir):
        # if we get a template with source e.g. dirwithmoretemplates/foo.tpl,
        #  we should still get just foo.tpl without the subdir as a result
        fn = 'asd'
        fntpl = 'dirwithmoretemplates/asd.tpl'
        self.make_sure_file_does_not_exists(tmpdir, fn)
        inp = {'template': {'source': fntpl},
               'data': {'foo': 'foo'},
               'output': fn,
               'destination': tmpdir.strpath}
        c = Command('jinja_render',
                    inp,
                    kwargs={'__files_dir__': [self.filesdir]})
        c.run()
        assert self.is_file_exists(tmpdir, fn) and self.get_file_contents(tmpdir, fn) == 'foo'

    def test_render_dir(self, tmpdir):
        dr = 'dirwithmoretemplates'
        self.make_sure_file_does_not_exists(tmpdir, dr)
        inp = {'template': {'source': dr},
               'data': {'foo': 'foo', 'bar': 'bar'},
               'destination': tmpdir.strpath}
        c = Command('jinja_render_dir',
                    inp,
                    kwargs={'__files_dir__': [self.filesdir]})
        c.run()
        assert self.is_file_exists(tmpdir, 'asd') and self.get_file_contents(tmpdir, 'asd') == 'foo'
        assert self.is_file_exists(tmpdir, 'foo/sdf') and self.get_file_contents(tmpdir, 'foo/sdf') == 'bar'

class TestLogCommandRunner(object):
    def setup_method(self, method):
        self.l = LogCommandRunner
        self.tlh = TestLoggingHandler.create_fresh_handler()

    def test_log(self):
        self.l.run(Command('log_w', 'foo!'))
        assert self.tlh.msgs == [('WARNING', 'foo!')]

    def test_log_wrong_level(self):
        with pytest.raises(CommandException):
            self.l.run(Command('log_b', 'bar'))


class TestNormalizeCommandRunner(object):
    def setup_method(self, method):
        self.n = NormalizeCommandRunner()

    def test_strips_digits_at_start(self):
        self.n.run(Command('normalize', '42blah')) == (True, 'blah')

    def test_replaces_bad_chars_with_underscores(self):
        bad_string = '-+\\|()[]{}<>,./:\'" \t;`!@#$%^&*'
        self.n.run(Command('normalize', bad_string)) == (True, '_' * len(bad_string))


class TestSCLCommandRunner(object):
    def setup_method(self, method):
        self.tlh = TestLoggingHandler.create_fresh_handler()

    def test_scl_passes_scls_list_to_command_invocation(self):
        # please don't use $__scls__ in actual assistants :)
        # scl runner has to use the unformatted input
        inp = [{'log_i': '$__scls__'}]
        fmtd_inp = [{'log_i': 'this should not be used'}]
        c = Command('scl enable foo bar', inp)
        c.run()
        assert ('INFO', "[['enable', 'foo', 'bar']]") in self.tlh.msgs
