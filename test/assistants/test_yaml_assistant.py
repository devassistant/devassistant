from flexmock import flexmock
import pytest

from devassistant import exceptions
from devassistant import settings
from devassistant.assistants import yaml_assistant
from devassistant.command_helpers import ClHelper, RPMHelper, YUMHelper

# hook app testing logging
from test.logger import TestLoggingHandler

class TestYamlAssistant(object):
    template_dir = yaml_assistant.YamlAssistant.template_dir

    def setup_method(self, method):
        self.ya = yaml_assistant.YamlAssistant()
        self.ya._files = {'first': {'source': 'f/g'}, 'second': {'source': 's/t'}}
        self.tlh = TestLoggingHandler.create_fresh_handler()

        self.ya2 = yaml_assistant.YamlAssistant()
        self.ya2._run = [{'if _ide':
                            [{'if ls /notachance': [{'log_d': 'ifif'}]},
                             {'else': [{'log_d': 'ifelse'}]}]},
                         {'else': [{'log_d': 'else'}]}]

    @pytest.mark.parametrize(('comm', 'arg_dict', 'result'), [
        ('ls -la', {}, 'ls -la'),
        ('touch $foo ${bar} $baz', {'foo': 'a', 'bar': 'b'}, 'touch a b $baz'),
        ('cp *first second', {}, 'cp {0}/f/g second'.format(template_dir)),
        ('cp *{first} *{nothing}', {}, 'cp %s/f/g *{nothing}' % (template_dir)),
        ('cp *{first} $foo', {'foo': 'a'}, 'cp {0}/f/g a'.format(template_dir)),
    ])
    def test_format(self, comm, arg_dict, result):
        assert self.ya._format(comm, **arg_dict) == result

    def test_format_handles_bool(self):
        # If command is false/true in yaml file, it gets coverted to False/True
        # which is bool object. format should handle this.
        assert self.ya._format(True) == 'true'
        assert self.ya._format(False) == 'false'

    def test_errors_pass(self):
        self.ya._fail_if = [{'cl': 'false'}, {'cl': 'grep'}]
        assert not self.ya.errors()

    def test_errors_fail(self):
        self.ya._fail_if = [{'cl': 'false'}, {'cl': 'true'}]
        assert self.ya.errors() == ['Cannot proceed because command returned 0: true']

    def test_errors_unknow_action(self):
        self.ya._fail_if = [{'foobar': 'not an action'}]
        assert not self.ya.errors()
        assert self.tlh.msgs == [('WARNING', 'Unknown action type foobar, skipping.')]

    # TODO: refactor to also test _dependencies_section alone
    def test_dependencies(self):
        self.ya._dependencies = [{'default': [{'rpm': ['foo', '@bar', 'baz']}]}]
        flexmock(RPMHelper).should_receive('is_rpm_installed').and_return(False, True).one_by_one()
        flexmock(YUMHelper).should_receive('is_group_installed').and_return(False)
        flexmock(YUMHelper).should_receive('install').with_args('foo', '@bar').and_return(True)
        self.ya.dependencies()

    def test_dependencies_uses_non_default_section_on_param(self):
        self.ya._dependencies = [{'default': [{'rpm': ['foo']}]}, {'_a': [{'rpm': ['bar']}]}]
        flexmock(RPMHelper).should_receive('is_rpm_installed').and_return(False, False).one_by_one()
        flexmock(YUMHelper).should_receive('install').with_args('foo').and_return(True)
        flexmock(YUMHelper).should_receive('install').with_args('bar').and_return(True)
        self.ya.dependencies(a=True)

    def test_dependencies_does_not_use_non_default_section_when_param_not_present(self):
        self.ya._dependencies = [{'default': [{'rpm': ['foo']}]}, {'_a': [{'rpm': ['bar']}]}]
        flexmock(RPMHelper).should_receive('is_rpm_installed').and_return(False, False).one_by_one()
        flexmock(YUMHelper).should_receive('install').with_args('foo').and_return(True)
        self.ya.dependencies()

    def test_run_pass(self):
        self.ya._run = [{'cl': 'true'}, {'cl': 'ls'}]
        self.ya.run()

    def test_run_fail(self):
        self.ya._run = [{'cl': 'true'}, {'cl': 'false'}]
        with pytest.raises(exceptions.RunException):
            self.ya.run()

    def test_run_unkown_action(self):
        self.ya._run = [{'foo': 'bar'}]
        self.ya.run()
        assert self.tlh.msgs == [('WARNING', 'Unknown action type foo, skipping.')]

    def test_get_section_to_run_chooses_selected(self):
        self.ya._run = [{'cl': 'ls'}]
        self.ya._run_foo = [{'cl': 'pwd'}]
        section = self.ya._get_section_to_run(section='run', kwargs_override=False, foo=True)
        assert section is self.ya._run

    def test_get_section_to_run_overrides_if_allowed(self):
        self.ya._run = [{'cl': 'ls'}]
        self.ya._run_foo = [{'cl': 'pwd'}]
        section = self.ya._get_section_to_run(section='run', kwargs_override=True, foo=True)
        assert section is self.ya._run_foo

    def test_run_runs_in_foreground_if_asked(self):
        self.ya._run = [{'cl_f': 'ls'}]
        flexmock(ClHelper).should_receive('run_command').with_args('ls', True, False)
        self.ya.run(foo='bar')

    def test_run_logs_command_at_debug(self):
        self.ya._run = [{'cl': 'ls'}]
        self.ya.run(foo='bar')
        assert self.tlh.msgs == [('DEBUG', settings.COMMAND_LOG_STRING.format(cmd='/usr/bin/ls'))]

    def test_run_logs_command_at_info_if_asked(self):
        self.ya._run = [{'cl_i': 'ls'}]
        self.ya.run(foo='bar')
        assert self.tlh.msgs == [('INFO', settings.COMMAND_LOG_STRING.format(cmd='/usr/bin/ls'))]

    def test_log(self):
        self.ya._fail_if = [{'log_w': 'foo!'}]
        self.ya.errors()
        assert self.tlh.msgs == [('WARNING', 'foo!')]

    def test_log_wrong_level(self):
        self.ya._fail_if = [{'log_b': 'bar'}]
        self.ya.errors()
        assert self.tlh.msgs == [('WARNING', 'Unknown logging command log_b with message bar')]

    def test_log_formats_message(self):
        self.ya._fail_if = [{'log_i': 'this is $how cool'}]
        self.ya.errors(how='very')
        assert self.tlh.msgs == [('INFO', 'this is very cool')]

    def test_run_if_nested_else(self):
        self.ya2.run(ide=True)
        assert ('DEBUG', 'ifelse') in self.tlh.msgs

    def test_run_else(self):
        self.ya2.run()
        assert ('DEBUG', 'else') in self.tlh.msgs
