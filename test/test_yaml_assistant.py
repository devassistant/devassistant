import logging
import os

from flexmock import flexmock
import pytest

from devassistant import exceptions
from devassistant import settings
from devassistant import yaml_assistant
from devassistant import snippet
from devassistant.command_helpers import ClHelper
from devassistant.yaml_snippet_loader import YamlSnippetLoader

# hook app testing logging
from test.logger import TestLoggingHandler

# TODO: some of this should probably be tested in command_runners/lang

class TestYamlAssistant(object):
    def setup_method(self, method):
        self.ya = yaml_assistant.YamlAssistant('ya', {}, '', None)
        self.ya.role = 'crt'
        self.ya._files = {'first': {'source': 'f/g'}, 'second': {'source': 's/t'}}
        self.tlh = TestLoggingHandler.create_fresh_handler()

        self.ya2 = yaml_assistant.YamlAssistant('ya2', {}, '', None)
        self.ya2._files = {}
        self.ya2.role = 'crt'
        self.ya2._run = [{'if $ide':
                            [{'if $(test -d /notachance)': [{'log_d': 'ifif'}]},
                             {'else': [{'log_d': 'ifelse'}]}]},
                         {'else': [{'log_d': 'else'}]}]

    # TODO: refactor to also test _dependencies_section alone
    def test_dependencies(self):
        self.ya._dependencies = [{'rpm': ['foo', '@bar', 'baz']}]
        self.ya.dependencies() == self.ya._dependencies

    def test_dependencies_uses_non_default_section_on_param(self):
        self.ya._dependencies = [{'rpm': ['foo']}]
        self.ya._dependencies_a = [{'rpm': ['bar']}]
        assert self.ya._dependencies[0] in self.ya.dependencies(kwargs={'a': True})
        assert self.ya._dependencies_a[0] in self.ya.dependencies(kwargs={'a': True})

    def test_dependencies_does_not_use_non_default_section_when_param_not_present(self):
        self.ya._dependencies = [{'rpm': ['foo']}]
        self.ya._dependencies_a = [{'rpm': ['bar']}]
        assert self.ya.dependencies() == self.ya._dependencies

    def test_dependencies_if(self):
        self.ya._dependencies = [{'if $x': [{'rpm': ['foo']}]}, {'else': [{'rpm': ['bar']}]}]
        assert self.ya.dependencies(kwargs={'x': 'x'}) == [{'rpm': ['foo']}]

    def test_dependencies_else(self):
        self.ya._dependencies = [{'if $x': [{'rpm': ['foo']}]}, {'else': [{'rpm': ['bar']}]}]
        assert self.ya.dependencies() == [{'rpm': ['bar']}]

    def test_run_pass(self):
        self.ya._run = [{'cl': 'true'}, {'cl': 'ls'}]
        self.ya.run()

    def test_run_fail(self):
        self.ya._run = [{'cl': 'true'}, {'cl': 'false'}]
        with pytest.raises(exceptions.RunException):
            self.ya.run()

    def test_run_unkown_command(self):
        self.ya._run = [{'foo': 'bar'}]
        self.ya.run()
        assert self.tlh.msgs == [('WARNING', 'Unknown command type foo, skipping.')]

    def test_run_logs_command_at_debug(self):
        # previously, this test used 'ls', but that is in different locations on different
        # distributions (due to Fedora's usrmove), so use something that should be common
        self.ya._run = [{'cl': 'id'}]
        self.ya.run(kwargs={'foo':'bar'})
        assert ('DEBUG', 'id') in self.tlh.msgs

    def test_run_logs_command_at_info_if_asked(self):
        self.ya._run = [{'cl_i': 'id'}]
        self.ya.run(kwargs={'foo': 'bar'})
        assert ('INFO', 'id') in self.tlh.msgs

    def test_log(self):
        self.ya._run = [{'log_w': 'foo!'}]
        self.ya.run()
        assert self.tlh.msgs == [('WARNING', 'foo!')]

    def test_log_wrong_level(self):
        self.ya._run = [{'log_b': 'bar'}]
        self.ya.run()
        assert self.tlh.msgs == [('WARNING', 'Unknown logging command log_b with message bar')]

    def test_log_formats_message(self):
        self.ya._run = [{'log_i': 'this is $how cool'}]
        self.ya.run(kwargs={'how': 'very'})
        assert self.tlh.msgs == [('INFO', 'this is very cool')]

    def test_run_if_nested_else(self):
        self.ya2.run(kwargs={'ide': True})
        assert ('DEBUG', 'ifelse') in self.tlh.msgs

    def test_successful_command_with_no_output_evaluates_to_true(self):
        self.ya._run = [{'if $(true)': [{'log_i': 'success'}]}]
        self.ya.run()
        assert('INFO', 'success') in self.tlh.msgs

    def test_run_else(self):
        self.ya2.run()
        assert ('DEBUG', 'else') in self.tlh.msgs

    def test_run_failed_if_doesnt_log_error(self):
        self.ya._run = [{'if $(test -d /dontlogfailure)': [{'dont': 'runthis'}]}]
        self.ya.run()
        assert 'ERROR' not in map(lambda x: x[0], self.tlh.msgs)


    def test_run_snippet_missing(self):
        self.ya._run = [{'use': 'foo.bar'}]
        self.ya.run()
        assert ('WARNING', 'Couldn\'t find run section "foo.bar".') in self.tlh.msgs

    def test_run_snippet(self):
        self.ya._run = [{'use': 'mysnippet'}]
        flexmock(YamlSnippetLoader).should_receive('get_snippet_by_name').\
                                    with_args('mysnippet').\
                                    and_return(snippet.Snippet('mysnippet',
                                                               {'run': [{'log_i': 'spam'}]},
                                                               'mysnippet.yaml'))
        self.ya.run()
        assert ('INFO', 'spam') in self.tlh.msgs

    def test_run_non_default_snippet_section(self):
        self.ya._run = [{'use': 'mysnippet.run_foo'}]
        flexmock(YamlSnippetLoader).should_receive('get_snippet_by_name').\
                                    with_args('mysnippet').\
                                    and_return(snippet.Snippet('mysnippet',
                                                               {'run': [{'log_i': 'spam'}],
                                                                'run_foo': [{'log_i': 'foo'}]},
                                                               'mysnippet.yaml'))
        self.ya.run()
        assert ('INFO', 'foo') in self.tlh.msgs

    def test_dependencies_snippet(self):
        self.ya._dependencies = [{'use': 'mysnippet.dependencies_foo'}]
        flexmock(YamlSnippetLoader).should_receive('get_snippet_by_name').\
                                    with_args('mysnippet').\
                                    and_return(snippet.Snippet('mysnippet',
                                                               {'dependencies_foo': [{'rpm': ['bar']}]},
                                                               'mysnippet.yaml'))
        assert self.ya.dependencies() == [{'rpm': ['bar']}]

    def test_dependencies_snippet_also_installs_default_dependencies(self):
        self.ya._dependencies = [{'use': 'mysnippet.dependencies_foo'}]
        flexmock(YamlSnippetLoader).should_receive('get_snippet_by_name').\
                                    with_args('mysnippet').\
                                    and_return(snippet.Snippet('mysnippet',
                                                               {'dependencies_foo': [{'rpm': ['bar']}],
                                                               'dependencies': [{'rpm': ['spam']}]},
                                                               'mysnippet.yaml'))
        assert {'rpm': ['bar']} in self.ya.dependencies()
        assert {'rpm': ['spam']} in self.ya.dependencies()

    def test_snippet_uses_its_own_files_section(self):
        self.ya._run = [{'use': 'mysnippet'}, {'log_w': '*first'}]
        flexmock(YamlSnippetLoader).should_receive('get_snippet_by_name').\
                                    with_args('mysnippet').\
                                    and_return(snippet.Snippet('mysnippet',
                                                               {'files':
                                                                   {'first': {'source': 'from/snippet'}},
                                                                'run': [{'log_i': '*first'}]},
                                                              'mysnippet.yaml'))
        self.ya.run()
        assert filter(lambda x: x[0] == 'INFO' and x[1].endswith('from/snippet'), self.tlh.msgs)
        # make sure that after the snippet ends, we use the old files section
        assert filter(lambda x: x[0] == 'WARNING' and x[1].endswith('f/g'), self.tlh.msgs)

    def test_assign_in_condition_modifies_outer_scope(self):
        self.ya._run = [{'if $foo': [{'$foo': '$spam'}]}, {'log_i': '$foo'}]
        self.ya.run(kwargs={'foo': 'foo', 'spam': 'spam'})
        assert('INFO', 'spam') in self.tlh.msgs

    def test_assign_in_snippet_or_run_doesnt_modify_outer_scope(self):
        self.ya._run = [{'use': 'self.run_blah'}, {'log_i': '$foo'}]
        self.ya._run_blah = [{'$foo': '$spam'}, {'log_i': 'yes, I ran'}]
        self.ya.run(kwargs={'foo': 'foo', 'spam': 'spam'})
        assert('INFO', 'yes, I ran') in self.tlh.msgs
        assert('INFO', 'foo') in self.tlh.msgs

    def test_scl_passes_scls_list_to_command_invocation(self):
        # please don't use $__scls__ in actual assistants :)
        self.ya._run = [{'scl enable foo bar': [{'log_i': '$__scls__'}]}]
        self.ya.run()
        assert ('INFO', "[['enable', 'foo', 'bar']]") in self.tlh.msgs

    def test_snippet_uses_own_files_dir(self):
        self.ya._run = [{'use': 'a.run'}, {'log_i': '*first'}]
        flexmock(YamlSnippetLoader).should_receive('get_snippet_by_name').\
                                    with_args('a').\
                                    and_return(snippet.Snippet('mysnippet',
                                                               {'files_dir': 'foo/bar/baz/spam',
                                                                'files':
                                                                    {'first': {'source': 'file'}},
                                                                'run': [{'log_i': '*first'}]},
                                                               'mysnippet.yaml'))
        self.ya.run()
        assert ('INFO', 'foo/bar/baz/spam/file') in self.tlh.msgs
        assert ('INFO', os.path.join(self.ya.files_dir, 'f/g')) in self.tlh.msgs

    def test_default_icon_path(self):
        self.ya.path = os.path.join(settings.DATA_DIRECTORIES[0], 'assistants/crt/bar/baz.yaml')
        assert self.ya.default_icon_path == os.path.join(settings.DATA_DIRECTORIES[0], 'icons/crt/bar/baz.svg')

    def test_loop_empty_string(self):
        self.ya._run = [{'for $i in $(echo "")': [{'log_i': '$i'}]}]
        self.ya.run()
        assert 'INFO' not in map(lambda x: x[0], self.tlh.msgs)

    def test_loop_words(self):
        self.ya._run = [{'for $i in $(echo "foo bar")': [{'log_i': '$i'}]}]
        self.ya.run()
        assert ('INFO', 'foo') in self.tlh.msgs
        assert ('INFO', 'bar') in self.tlh.msgs

    def test_loop_two_control_vars_fails_on_string(self):
        self.ya._run = [{'for $i, $j in $(echo "foo bar")': [{'log_i': '$i'}]}]
        with pytest.raises(exceptions.YamlSyntaxError):
            self.ya.run()

    def test_loop_two_control_vars_fails_on_string(self):
        self.ya._run = [{'for $i, $j in $foo': [{'log_i': '$i, $j'}]}]
        self.ya.run(kwargs={'foo': {'bar': 'barval', 'spam': 'spamval'}})
        assert ('INFO', 'bar, barval') in self.tlh.msgs
        assert ('INFO', 'spam, spamval') in self.tlh.msgs


class TestExpressions(TestYamlAssistant):
    def test_assign_existing_nonempty_variable(self):
        self.ya._run = [{'$foo': '$bar'}, {'log_i': '$foo'}]
        self.ya.run(kwargs={'bar': 'bar'})
        assert ('INFO', 'bar') in self.tlh.msgs

        # both logical result and result
        self.ya._run = [{'$success, $val': '$foo'},
                        {'log_i': '$success'},
                        {'log_i': '$val'}]
        self.ya.run(kwargs={'foo': 'foo'})
        assert ('INFO', 'True') in self.tlh.msgs
        assert ('INFO', 'foo') in self.tlh.msgs

    def test_assign_existing_empty_variable(self):
        self.ya._run = [{'$foo': '$bar'}, {'log_i': '$foo'}]
        self.ya.run(kwargs={'bar': ''})
        assert ('INFO', '') in self.tlh.msgs

        # both logical result and result
        self.ya._run = [{'$success, $val': '$foo'},
                        {'log_i': '$success'},
                        {'log_i': '$val'}]
        self.ya.run(kwargs={'foo': ''})
        assert ('INFO', 'False') in self.tlh.msgs
        assert ('INFO', '') in self.tlh.msgs

    def test_assign_nonexisting_variable(self):
        self.ya._run = [{'$foo': '$bar'}, {'log_i': '$foo'}]
        self.ya.run()
        assert ('INFO', '') in self.tlh.msgs

        # both logical result and result
        self.ya._run = [{'$success, $val': '$foo'},
                        {'log_i': '$success'},
                        {'log_i': '$val'}]
        self.ya.run()
        assert ('INFO', 'False') in self.tlh.msgs
        assert ('INFO', '') in self.tlh.msgs

    def test_assign_defined_empty_variable(self):
        self.ya._run = [{'$success, $val': 'defined $foo'},
                        {'log_i': '$success'},
                        {'log_i': '$val'}]
        self.ya.run(kwargs={'foo': ''})
        assert ('INFO', 'True') in self.tlh.msgs
        assert ('INFO', '') in self.tlh.msgs

    def test_assign_defined_variable(self):
        self.ya._run = [{'$success, $val': 'defined $foo'},
                        {'log_i': '$success'},
                        {'log_i': '$val'}]
        self.ya.run(kwargs={'foo': 'foo'})
        assert ('INFO', 'True') in self.tlh.msgs
        assert ('INFO', 'foo') in self.tlh.msgs

    def test_assign_defined_nonexistent_variable(self):
        self.ya._run = [{'$success, $val': 'defined $foo'},
                        {'log_i': '$success'},
                        {'log_i': '$val'}]
        self.ya.run()
        assert ('INFO', 'False') in self.tlh.msgs
        assert ('INFO', '') in self.tlh.msgs

    def test_assign_successful_command(self):
        self.ya._run = [{'$foo': '$(basename foo/bar)'}, {'log_i': '$foo'}]
        self.ya.run()
        assert ('INFO', 'bar') in self.tlh.msgs

        # both logical result and result
        self.ya._run = [{'$success, $val': '$(basename foo/bar)'},
                        {'log_i': '$success'},
                        {'log_i': '$val'},
                        {'if $success': [{'log_i': 'success!'}]}]
        self.ya.run()
        assert ('INFO', 'True') in self.tlh.msgs
        assert ('INFO', 'bar') in self.tlh.msgs
        assert ('INFO', 'success!') in self.tlh.msgs

    def test_assign_unsuccessful_command(self):
        self.ya._run = [{'$foo': '$(ls spam/spam/spam)'}, {'log_i': '$foo'}]
        self.ya.run()
        assert ('INFO', u'ls: cannot access spam/spam/spam: No such file or directory') in self.tlh.msgs

        # both logical result and result
        self.ya._run = [{'$success, $val': '$(ls spam/spam/spam)'},
                        {'log_i': '$success'},
                        {'log_i': '$val'},
                        {'if $success': [{'log_i': 'oh no, spam found'}]},
                        {'else': [{'log_i': 'good, no spam'}]}]
        self.ya.run()
        assert ('INFO', u'ls: cannot access spam/spam/spam: No such file or directory') in self.tlh.msgs
        assert ('INFO', 'False') in self.tlh.msgs
        assert ('INFO', 'good, no spam') in self.tlh.msgs

class TestYamlAssistantModifier(object):
    def setup_method(self, method):
        self.ya = yaml_assistant.YamlAssistant('ya', {}, '', None)
        self.ya.role = 'mod'
        self.ya._files = {}
        self.tlh = TestLoggingHandler.create_fresh_handler()
        self.dda = {'subassistant_path': ['foo', 'bar', 'baz']}

    def test_dependencies_install_dependencies_for_subassistant_path(self):
        flexmock(self.ya).should_receive('proper_kwargs').and_return(self.dda)
        self.ya._dependencies = [{'rpm': ['spam']}]
        self.ya._dependencies_foo = [{'rpm': ['beans']}]
        self.ya._dependencies_foo_bar_baz = [{'rpm': ['eggs']}]
        deps = self.ya.dependencies(kwargs=self.dda)
        assert {'rpm': ['spam']} in deps
        assert {'rpm': ['beans']} in deps
        assert {'rpm': ['eggs']} in deps

    def test_run_chooses_proper_method(self):
        flexmock(self.ya).should_receive('proper_kwargs').and_return(self.dda)
        self.ya._run = [{'log_i': 'wrong!'}]
        self.ya._run_foo = [{'log_i': 'wrong too!'}]
        self.ya._run_foo_bar_baz = [{'log_i': 'correct'}]
        self.ya.run(kwargs=self.dda)
        assert ('INFO', 'correct') in self.tlh.msgs
