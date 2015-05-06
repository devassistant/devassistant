# -*- coding: utf8 -*-
import copy
import os
import six
import sys

import pytest
from flexmock import flexmock
import yaml

from devassistant.assistant_base import AssistantBase
from devassistant.command_helpers import ClHelper, DialogHelper, DockerHelper
from devassistant.command_runners import AskCommandRunner, ClCommandRunner, \
    Jinja2Runner, LogCommandRunner, NormalizeCommandRunner, UseCommandRunner, \
    SetupProjectDirCommandRunner, PingPongCommandRunner, LoadCmdCommandRunner, \
    EnvCommandRunner, DockerCommandRunner, DotDevassistantCommandRunner, \
    GitHubCommandRunner
# also import just command_runners to have access to command_runners.command_runners
from devassistant import command_runners, lang, utils
from devassistant.exceptions import CommandException, RunException
from devassistant.lang import Command
from devassistant.yaml_assistant import YamlAssistant

from test.logger import LoggingHandler

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
        comm = Command('ask_password', {}, {'__ui__': 'cli'})
        res = self.acr(comm).run()

        assert res[0] is True
        assert res[1] == 'foobar'

    @pytest.mark.parametrize('inp', ['', 'foo', u'foo'])
    def test_run_input(self, inp):
        flexmock(DialogHelper)
        DialogHelper.should_receive('ask_for_input_with_prompt').and_return(inp)
        comm = Command('ask_input', {}, {'__ui__': 'cli'})
        res = self.acr(comm).run()

        assert res[0] is bool(inp)
        assert res[1] == inp

    @pytest.mark.parametrize('decision', [True, False])
    def test_run_confirm(self, decision):
        flexmock(DialogHelper)
        DialogHelper.should_receive('ask_for_confirm_with_message').and_return(decision)
        comm = Command('ask_confirm', {}, {'__ui__': 'cli'})
        res = self.acr(comm).run()

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
        self.tlh = LoggingHandler.create_fresh_handler()

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
                             ('self', 'bar', 'mid', 'mid'),
                             ('super', 'foo', 'leaf', 'parent'),
                             ('super', 'bar', 'leaf', 'mid')])
    def test_get_assistant(self, assistant, section, origin, expected):
        assert self.ccr.get_assistant(assistant, section, self.ass[origin]) == self.ass[expected]

    @pytest.mark.parametrize(('assistant', 'section', 'origin'), [
                             ('super', 'baz', 'leaf'),
                             ('self', 'foo', 'leaf'),
                             ('self', 'baz', 'parent')])
    def test_get_assistant_fails(self, assistant, section, origin):
        with pytest.raises(CommandException):
            self.ccr.get_assistant(assistant, section, self.ass[origin])

    @pytest.mark.parametrize(('assistant', 'section'), [
                             ('parent', 'foo'),
                             ('mid', 'bar')])
    def test_get_assistant_section(self, assistant, section):
        assert self.ccr.get_assistant_section(section, self.ass[assistant]) == \
               getattr(self.ass[assistant], '_' + section)

    def test_get_assistant_section_fails(self):
        with pytest.raises(CommandException):
            self.ccr.get_assistant_section('foo', self.ass['leaf'])

    @pytest.mark.parametrize(('cmd', 'assistant', 'expected'), [
                             ('super.foo', 'leaf', 'bar'),
                             ('super.bar', 'leaf', 'baz')])
    def test_run_assistants(self, cmd, assistant, expected):
        com = Command('use', cmd, {'__assistant__': self.ass[assistant]})
        flexmock(lang).should_receive('run_section').and_return(expected)
        result = self.ccr(com).run()

        assert result == expected

    def test_run_with_specified_args(self):
        kwargs = {'spam': 'something',
                  'nospam': 'hahaha',
                  '__magic_val__': 'it\'s magical',
                  '__assistant__': self.ass['leaf']}

        com = Command('use', {'sect': 'self.run',
                              'args': {'spam': 'something else', 'spam2': 'blah'}}, kwargs)

        class Matcher(object):
            def __eq__(self, other):
                assert len(other) == 4
                assert other['spam'] == 'something else'
                assert other['spam2'] == 'blah'
                assert other['__magic_val__'] == 'it\'s magical'
                assert '__assistant__' in other
                return True

        flexmock(lang).should_receive('run_section').with_args(list, Matcher())
        com.run()


class TestClCommandRunner(object):
    def setup_method(self, method):
        self.cl = ClCommandRunner
        self.tlh = LoggingHandler.create_fresh_handler()

    def test_command_passes(self):
        self.cl(Command('cl', 'true')).run()

    def test_command_fails(self):
        with pytest.raises(RunException):
            self.cl(Command('cl', 'false')).run()

    def test_run_logs_command_at_debug(self):
        # previously, this test used 'ls', but that is in different locations on different
        # distributions (due to Fedora's usrmove), so use something that should be common
        self.cl(Command('cl', 'id')).run()
        assert ('DEBUG', 'id') in self.tlh.msgs

    def test_run_logs_command_at_info_if_asked(self):
        self.cl(Command('cl_i', 'id')).run()
        assert ('INFO', 'id') in self.tlh.msgs

    def test_p_flag_pasesses_even_if_subcommand_fails(self):
        self.cl(Command('cl_ip', 'false')).run()
        assert ('INFO', 'false') in self.tlh.msgs

    def test_passes_env(self):
        self.cl(Command('cl_i', 'echo $DEVASSISTANTTESTFOO',
            kwargs={'__env__': {'DEVASSISTANTTESTFOO': 'foo'}})).run()
        assert ('INFO', 'foo') in self.tlh.msgs


class TestDependenciesCommandRunner(object):
    pass


class TestDotDevassistantCommandRunner(object):

    def setup_class(self):
        self.get_cmd = lambda self, struct: Command('dda_w', struct, {'foo': 'bar'})
        self.ddcr = DotDevassistantCommandRunner

    @pytest.mark.parametrize('struct', [
        ['foo', {'bar': 'baz'}],
        {'path': 'foo', 'write': {'bar': 'baz'}},
    ])
    def test_dda_w_check_args(self, struct):
        cmd = self.get_cmd(struct)
        self.ddcr.check_args(cmd)

    @pytest.mark.parametrize('struct', [
        ['foo'],
        {'path': 'foo', 'bar': 'baz', 'qux': '123'},
        3,
        'foo',
        None
    ])
    def test_dda_w_check_args_fails(self, struct):
        cmd = self.get_cmd(struct)
        with pytest.raises(CommandException):
            self.ddcr.check_args(cmd)

    def test_dda_w_fails_with_invalid_keys(self):
        cmd = self.get_cmd({'foo': 'bar', 'baz': 'qux'})
        with pytest.raises(CommandException) as e:
            self.ddcr(cmd).run()

        assert 'dda_w expects mapping' in str(e)

    def test_dda_w_takes_section_as_literal(self, tmpdir):
        # we want to make sure that the section we write is not evaluated, not even substituted
        to_write = [tmpdir.strpath, {'run': [{'$cwd~': '$(pwd)'}, {'log_i': '$foo'}]}]
        open(os.path.join(tmpdir.strpath, '.devassistant'), 'w').close()
        self.get_cmd(to_write).run()
        content = open(os.path.join(tmpdir.strpath, '.devassistant')).read()
        assert content == yaml.dump(to_write[1], default_flow_style=False)

    def test_list_and_dict_inputs_are_same(self, tmpdir):
        kwargs = {'foo': 'bar'}

        # List
        list_path = str(tmpdir.mkdir('list'))
        open(os.path.join(list_path, '.devassistant'), 'w').close()
        to_write_list = [list_path, {'dependencies': [{'rpm': ['foo']}],
                                     'run': [{'log_i': 'foo'}]}]
        self.get_cmd(to_write_list).run()
        list_content = open(os.path.join(list_path, '.devassistant')).read()

        # Dict
        dict_path = str(tmpdir.mkdir('dict'))
        open(os.path.join(dict_path, '.devassistant'), 'w').close()
        to_write_dict = [dict_path, {'dependencies': [{'rpm': ['foo']}],
                                     'run': [{'log_i': 'foo'}]}]
        self.get_cmd(to_write_dict).run()
        dict_content = open(os.path.join(dict_path, '.devassistant')).read()

        assert list_content == dict_content
        assert list_content == yaml.dump(to_write_list[1], default_flow_style=False)


class TestGitHubCommandRunner(object):

    def setup_class(self):
        self.get_cmd = lambda self, struct: Command('github', struct, {'__ui__': 'cli'})
        self.ghcr = GitHubCommandRunner

    @pytest.mark.parametrize(('struct', 'comm', 'keys'), [
        ({'do': 'create_repo', 'login': 'foo', 'reponame': 'bar'},
            'create_repo',
            ['login', 'reponame']),

        (['create_repo', {'login': 'foo', 'reponame': 'bar'}],
            'create_repo',
            ['login', 'reponame']),

        ('push', 'push', []),

        ({'do': 'create_fork', 'repo_url': 'http://example.com', 'login': 'foo'},
            'create_fork',
            ['login', 'repo_url'])
    ])
    def test_allowed_formats(self, struct, comm, keys):
        cmd = self.get_cmd(struct)
        result_comm, result_args = self.ghcr.format_args(cmd)

        assert result_comm == comm
        assert set(keys).issubset(set(result_args.keys()))

    @pytest.mark.parametrize('struct', [
        ['foo', 'bar', 'baz'],
        ['foo'],
        {'foo': 'bar'},
        2,
        [],
        {},
        None
    ])
    def test_forbidden_formats(self, struct):
        cmd = self.get_cmd(struct)
        with pytest.raises(CommandException):
            self.ghcr.format_args(cmd)

    @pytest.mark.parametrize('action', ['create_repo', 'create_and_push', 'push', 'create_fork'])
    def test_valid_actions(self, action):
        '''This test uses try/except on purpose. Valid outcomes are both a run with no exception
        raised, or a run with exception raised if that exception doesn't pertain to the action'''
        cmd = self.get_cmd({'do': action})
        try:
            self.ghcr.format_args(cmd)
        except CommandException as e:
            assert 'Invalid action' not in str(e)

    @pytest.mark.parametrize('action', ['foo', 2, None])
    def test_invalid_actions(self, action):
        cmd = self.get_cmd({'do': action})
        with pytest.raises(CommandException) as e:
            self.ghcr.format_args(cmd)

        assert 'Invalid action' in str(e)

    def test_arg_dict_same_as_list(self):
        arg_dict = {'do': 'create_repo', 'login': 'foo', 'reponame': 'bar'}
        arg_list = ['create_repo', {'login': 'foo', 'reponame': 'bar'}]

        list_cmd = self.get_cmd(arg_list)
        dict_cmd = self.get_cmd(arg_dict)

        list_res = self.ghcr.format_args(list_cmd)
        dict_res = self.ghcr.format_args(dict_cmd)

        assert list_res == dict_res
        assert len(list_res) == 2
        assert list_res[0] == 'create_repo'
        assert list_res[1]['login'] == 'foo'
        assert list_res[1]['reponame'] == 'bar'


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
        assert self.is_file_exists(tmpdir, fn) and \
               self.get_file_contents(tmpdir, fn) == 'print("foo")'

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
        assert self.is_file_exists(tmpdir, fn) and \
               self.get_file_contents(tmpdir, fn) == 'print("foo")'

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
        assert self.is_file_exists(tmpdir, fn) and \
               self.get_file_contents(tmpdir, fn) == 'print("foo")'

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
        assert self.is_file_exists(tmpdir, 'asd') and \
               self.get_file_contents(tmpdir, 'asd') == 'foo'
        assert self.is_file_exists(tmpdir, 'foo/sdf') and \
               self.get_file_contents(tmpdir, 'foo/sdf') == 'bar'

class TestLogCommandRunner(object):
    def setup_method(self, method):
        self.l = LogCommandRunner
        self.tlh = LoggingHandler.create_fresh_handler()

    def test_log(self):
        self.l(Command('log_w', 'foo!')).run()
        assert self.tlh.msgs == [('WARNING', 'foo!')]

    def test_log_wrong_level(self):
        with pytest.raises(CommandException):
            self.l(Command('log_b', 'bar')).run()


class TestNormalizeCommandRunner(object):
    def setup_method(self, method):
        self.n = NormalizeCommandRunner

    def test_strips_digits_at_start(self):
        self.n(Command('normalize', '42blah')).run() == (True, 'blah')

    def test_replaces_bad_chars_with_underscores(self):
        bad_string = '-+\\|()[]{}<>,./:\'" \t;`!@#$%^&*'
        self.n(Command('normalize', bad_string)).run() == (True, '_' * len(bad_string))

    def test_unicode_chars(self):
        s = 'ěšč'
        assert self.n(Command('normalize', s)).run() == (True, 'esc')
        s = u'ěšč'
        assert self.n(Command('normalize', s)).run() == (True, 'esc')

    def test_ok_chars(self):
        i = {'what': 'foo-bar.+*', 'ok_chars': '-.'}
        assert self.n(Command('normalize', i)).run() == (True, 'foo-bar.__')


class TestSCLCommandRunner(object):
    def setup_method(self, method):
        self.tlh = LoggingHandler.create_fresh_handler()

    def test_scl_with_nested_calls(self):
        # https://github.com/bkabrda/devassistant/issues/234
        # tests proper nesting of SCL commands and also elimination of identical calls
        inp = [{'scl enable hamham foo': [{'scl enable spamspam': [{'cl': 'ls'}]}]}]
        c = Command('scl enable spamspam', inp)
        with pytest.raises(RunException):
            c.run()
        # make sure to remove scl command processors from ClHelper
        ClHelper.command_processors = {}
        res_lines = [['scl enable spamspam - << DA_SCL_enable_spamspam_EOF',
                      'scl enable hamham foo - << DA_SCL_enable_hamham_foo_EOF',
                      'ls',
                      'DA_SCL_enable_hamham_foo_EOF',
                      'DA_SCL_enable_spamspam_EOF']]
        # shuffle first two and last two lines to get possible permutations of scl
        #  call order (command processors are in dict, which has arbitrary order)
        res_lines.append(copy.deepcopy(res_lines[0]))
        res_lines[1][0], res_lines[1][1] = res_lines[1][1], res_lines[1][0]
        res_lines[1][3], res_lines[1][4] = res_lines[1][4], res_lines[1][3]
        assert ('DEBUG', '\n'.join(res_lines[0])) in self.tlh.msgs or \
               ('DEBUG', '\n'.join(res_lines[1])) in self.tlh.msgs


class TestSetupProjectDirCommandRunner(object):
    def setup_method(self, method):
        self.s = SetupProjectDirCommandRunner

    @pytest.mark.parametrize('inp', [
        ({}),
        ({'from': 'foo/bar', 'accept_path': False}),
    ])
    def test_failure_cases(self, inp):
        c = Command('setup_project_dir', inp)
        with pytest.raises(CommandException):
            c.run()

    def test_fails_when_dir_exists(self, tmpdir):
        c = Command('setup_project_dir', {'from': 'foo'})
        with tmpdir.as_cwd():
            open('foo', 'w').close()
            with pytest.raises(CommandException):
                c.run()

    def test_doesn_fail_when_dir_exists_but_overrided(self, tmpdir):
        c = Command('setup_project_dir', {'from': 'foo', 'on_existing': 'pass'})
        with tmpdir.as_cwd():
            os.makedirs('foo')
            assert c.run() == (True, 'foo')

    @pytest.mark.parametrize('path, comm_args, normalized, varnames', [
        # two normal cases
        ('bar', {}, 'bar', []),
        (os.path.join('foo', 'bar'), {}, 'bar', []),
        # renamed variables
        (os.path.join('foo', 'bar'),
            {'contdir_var': 'a', 'topdir_var': 'b', 'topdir_normalized_var': 'c'},
            'bar',
            ['a', 'b', 'c']),
        # create_topdir variations
        (os.path.join('foo', 'bar'), {'create_topdir': False}, 'bar', []),
        (os.path.join('foo', 'bar'), {'create_topdir': 'normalized'}, 'bar', []),
    ])
    def test_correct_cases(self, tmpdir, path, comm_args, normalized, varnames):
        if not varnames:
            varnames = ['contdir', 'topdir', 'topdir_normalized']
        kwargs = {'name': path}
        comm_args['from'] = '$name'
        c = Command('setup_project_dir', comm_args, kwargs=kwargs)

        with tmpdir.as_cwd():
            ret = c.run()
            create_topdir = comm_args.get('create_topdir', True)
            p = path
            if create_topdir is True:
                assert ret == (True, p)
            elif create_topdir == 'normalized':
                p = os.path.join(os.path.dirname(path), normalized)
                assert ret == (True, p)
            else:
                p = os.path.dirname(path)
                assert ret == (True, p)
            assert os.path.isdir(p)
            # if os.path.dirname(path) == '', then '.' should be saved instead
            assert kwargs[varnames[0]] == (os.path.dirname(path) or '.')
            assert kwargs[varnames[1]] == os.path.basename(path)
            assert kwargs[varnames[2]] == normalized


class TestPingPongCommandRunner(object):
    fixtures = os.path.join(os.path.dirname(__file__), 'fixtures', 'pingpong')

    def setup_method(self, method):
        self.tlh = LoggingHandler.create_fresh_handler()

    def _run_pingpong(self, script, ctxt):
        return Command('pingpong',
            '{0} {1}'.format(sys.executable, os.path.join(self.fixtures, script)),
            ctxt).run()

    def test_ok_run(self):
        ctxt = {'foo': 'bar'}
        res = self._run_pingpong('ok_run.py', ctxt)

        assert res == (True, 'Everything OK')
        assert 'foo' not in ctxt
        assert ctxt['set_by_pp_client'] == 'bar'

        assert ('INFO', 'from var: bar') in self.tlh.msgs
        assert ('INFO', 'from ctxt: bar') in self.tlh.msgs
        assert ('DEBUG', 'foo') in self.tlh.msgs

    def test_no_return(self):
        with pytest.raises(CommandException) as e:
            self._run_pingpong('no_return.py', {})
        assert 'PingPong run method ended with unexpected result: None (expected 2-tuple)' in \
            str(e.value)

    def test_tracebacks(self):
        with pytest.raises(CommandException) as e:
            self._run_pingpong('tracebacks.py', {})
        assert 'PingPong run method ended with an exception:' in str(e.value)
        assert 'BaseException: problem' in str(e.value)


class TestLoadCmdCommandRunner(object):
    fixtures = os.path.join(os.path.dirname(__file__), 'fixtures', 'files', 'crt', 'commands')

    def setup_method(self, method):
        self.old_command_runners = command_runners.command_runners
        command_runners.command_runners = copy.deepcopy(self.old_command_runners)
        self.tlh = LoggingHandler.create_fresh_handler()

    def teardown_method(self, method):
        command_runners.command_runners = self.old_command_runners

    def _test_loaded_commands_work(self, prefix='', which=['CR1', 'CR2']):
        if 'CR1' in which:
            r1 = Command(prefix + 'barbarbar', 'foo').run()
            assert ('INFO', 'CR1: Doing something ...') in self.tlh.msgs
            assert r1 == (True, 'foobar')
        else:
            with pytest.raises(CommandException):
                Command(prefix + 'barbarbar', 'foo').run()

        if 'CR2' in which:
            r2 = Command(prefix + 'spamspamspam', 'foo').run()
            assert ('INFO', 'CR2: Doing something ...') in self.tlh.msgs
            assert r2 == (True, 'foospam')
        else:
            with pytest.raises(CommandException):
                Command(prefix + 'spamspamspam', 'foo').run()

    def test_basic(self):
        r = Command('load_cmd', {'source': 'a.py'},
                    {'__files_dir__': [self.fixtures]}).run()
        assert r[0] == True
        assert set(r[1]) == set(['CR1', 'CR2'])

        self._test_loaded_commands_work()

    def test_specified_by_string(self):
        r = Command('load_cmd', 'crt/commands/a.py').run()
        assert r[0] == True
        assert set(r[1]) == set(['CR1', 'CR2'])

        self._test_loaded_commands_work()

    def test_load_only(self):
        r = Command('load_cmd', {'from_file': {'source': 'a.py'}, 'load_only': 'CR1'},
                    {'__files_dir__': [self.fixtures]}).run()
        assert r == (True, ['CR1'])

        self._test_loaded_commands_work(which=['CR1'])

    def test_prefix(self):
        r = Command('load_cmd', {'from_file': 'crt/commands/a.py', 'prefix': 'prefix'}).run()
        assert r[0] == True
        assert set(r[1]) == set(['CR1', 'CR2'])

        self._test_loaded_commands_work(prefix='prefix.')
        # also test that they're not loaded in the '' prefix
        self._test_loaded_commands_work(which=[])

    def test_overrides_core_runners(self):
        Command('load_cmd', 'crt/commands/log.py').run()
        r = Command('log_i', 'message').run()

        assert ('INFO', 'Got you!') in self.tlh.msgs
        assert ('INFO', 'message') not in self.tlh.msgs
        assert r == (True, 'heee heee')


class TestEnvCommandRunner(object):
    def setup_method(self, method):
        self.kwargs = {'__env__': {'foo': 'bar', 'spam': 'spam'}}

    def test_set(self):
        res = EnvCommandRunner(Command('env_set', {'foo': 'changed', 'some': 'value'},
            self.kwargs)).run()
        assert res == (True, {'foo': 'changed', 'some': 'value'})
        assert self.kwargs == {'__env__': {'foo': 'changed', 'some': 'value', 'spam': 'spam'}}

    def test_unset_one(self):
        res = EnvCommandRunner(Command('env_unset', 'spam', self.kwargs)).run()
        assert res == (True, {'spam': 'spam'})
        assert self.kwargs == {'__env__': {'foo': 'bar'}}

    def test_unset_more(self):
        res = EnvCommandRunner(Command('env_unset', ['foo', 'spam'], self.kwargs)).run()
        assert res == (True, {'foo': 'bar', 'spam': 'spam'})
        assert self.kwargs == {'__env__': {}}


class TestDockerCommandRunner(object):

    def test_check_fails_when_docker_py_not_present(self):
        dh = flexmock(DockerHelper)
        dh.should_receive('_docker_module').and_return(None)
        dh.should_call('add_user_to_docker_group').never()
        dh.should_call('docker_service_enable_and_run').never()

        with pytest.raises(CommandException) as excinfo:
            DockerCommandRunner._docker_check_setup()

        assert 'module is not present' in str(excinfo.value)

    def test_check_passes_when_docker_present(self):
        dh = flexmock(DockerHelper)
        dh.should_receive('_docker_module').and_return(object())
        print(DockerHelper._docker_module, DockerHelper.is_available())
        dh.should_receive('docker_group_active').and_return(True)
        dh.should_receive('docker_service_running').and_return(True)
        dh.should_call('add_user_to_docker_group').never()
        dh.should_call('docker_service_enable_and_run').never()

        DockerCommandRunner._docker_check_setup()


