import os

from flexmock import flexmock
import pytest

from devassistant import exceptions
from devassistant import settings
from devassistant import yaml_assistant
from devassistant import snippet
from devassistant.yaml_snippet_loader import YamlSnippetLoader

# hook app testing logging
from test.logger import LoggingHandler


class TestYamlAssistant(object):
    def setup_method(self, method):
        self.ya = yaml_assistant.YamlAssistant('ya', {}, '', None)
        self.ya.role = 'crt'
        self.ya._files = {'first': {'source': 'f/g'}, 'second': {'source': 's/t'}}
        self.ya._dependencies = [{'rpm': ['foo']}]
        self.ya._dependencies_a = [{'rpm': ['bar']}]
        self.ya._pre_run = [{'log_i': 'pre'}]
        self.ya._run = [{'log_i': 'run'}]
        self.ya._post_run = [{'log_i': 'post'}]
        self.tlh = LoggingHandler.create_fresh_handler()

    def test_icon_path_is_empty_if_no_icon(self):
        self.ya.path = os.path.join(settings.DATA_DIRECTORIES[0], 'assistants/crt/b/b.yaml')
        assert self.ya.icon_path == ''
        assert self.ya.default_icon_path == ''

    @pytest.mark.parametrize('a, f', [
        ('c', '.svg'),
        ('f', '.png'),
    ])
    def test_finds_supported_icon_formats(self, a, f):
        ya = yaml_assistant.YamlAssistant(a, {},
            os.path.join(settings.DATA_DIRECTORIES[0], 'assistants/crt/{0}.yaml').format(a), None)
        assert ya.icon_path == os.path.join(settings.DATA_DIRECTORIES[0], 'icons/crt',
            a + f)
        assert ya.default_icon_path == ya.icon_path

    def test_snippet_uses_its_own_files_section(self):
        self.ya._run = [{'use': 'mysnippet.run'}, {'log_w': '*first'}]
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

    def test_run_snippet_missing(self):
        self.ya._run = [{'use': 'foo.bar'}]
        with pytest.raises(exceptions.CommandException):
            self.ya.run()

    def test_run_snippet(self):
        self.ya._run = [{'use': 'mysnippet.run'}]
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

    def test_assign_in_snippet_or_run_doesnt_modify_outer_scope(self):
        self.ya._run = [{'use': 'self.run_blah'}, {'log_i': '$foo'}]
        self.ya._run_blah = [{'$foo': '$spam'}, {'log_i': 'yes, I ran'}]
        self.ya.run(kwargs={'foo': 'foo', 'spam': 'spam'})
        assert('INFO', 'yes, I ran') in self.tlh.msgs
        assert('INFO', 'foo') in self.tlh.msgs

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

    def test_dependencies(self):
        self.ya.dependencies() == self.ya._dependencies

    def test_dependencies_uses_non_default_section_on_param(self):
        assert self.ya._dependencies[0] in self.ya.dependencies(kwargs={'a': True})
        assert self.ya._dependencies_a[0] in self.ya.dependencies(kwargs={'a': True})

    def test_dependencies_does_not_use_non_default_section_when_param_not_present(self):
        assert self.ya.dependencies() == self.ya._dependencies

    @pytest.mark.parametrize('stage, result', [
        ('pre', (True, 'pre')),
        ('', (True, 'run')),
        ('post', (True, 'post')),
    ])
    def test_run_uses_proper_section(self, stage, result):
        assert self.ya.run(stage) == result

    def test_parsed_yaml_None_values(self):
        # https://bugzilla.redhat.com/show_bug.cgi?id=1059305
        # if any section was totally empty (e.g. None), devassistant failed
        class ADict(dict): # use a dict subclass because of the check() in assistants
            def get(self, arg, default=None):
                return default
            def items(self):
                return [('run_foo', None)]
        self.ya.parsed_yaml = ADict()
        test_types = {'fullname': str, 'description': str, 'args': list, 'icon_path': str,
                      'files_dir': str, '_files': dict, '_logging': list, '_dependencies': list,
                      '_run': list, '_run_foo': list, '_pre_run': list, '_post_run': list}
        for k, v in test_types.items():
            assert isinstance(getattr(self.ya, k), v)

    @pytest.mark.parametrize('struct_args', [
        [{'foo': {'flags': ['--bar']}}, {'baz': {'flags': ['--qux']}}],
        {'foo': {'flags': ['--bar']}, 'baz': {'flags': ['--qux']}},
    ])
    def test_construct_args(self, struct_args):
        args = self.ya._construct_args(struct_args)

        assert isinstance(args, list)
        assert len(args) == 2

        for arg in args:
            assert arg.name in ['foo', 'baz']
            assert len(arg.flags) == 1
            assert arg.flags[0] in ['--bar', '--qux']

    def test_args_order_from_list(self):
        args_list = [{'foo': {'flags': {}}}, {'bar': {'flags': {}}}, {'baz': {'flags': {}}}]
        args = self.ya._construct_args(args_list)

        assert [arg.name for arg in args] == ['foo', 'bar', 'baz']


class TestYamlAssistantTweak(object):
    def setup_method(self, method):
        self.ya = yaml_assistant.YamlAssistant('ya', {}, '', None)
        self.ya.role = 'twk'
        self.ya._files = {}
        self.tlh = LoggingHandler.create_fresh_handler()
        self.dda = {'project_type': ['foo', 'bar', 'baz']}

    def test_dependencies_install_dependencies_for_project_type(self):
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
