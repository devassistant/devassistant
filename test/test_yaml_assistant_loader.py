import os

import pytest
import yaml

from devassistant.yaml_assistant_loader import YamlAssistantLoader

from test.logger import TestLoggingHandler

class TestYamlAssistantLoader(object):
    def setup_method(self, method):
        self.yl = YamlAssistantLoader
        self.reset_yl_assistants_dirs()
        self.tlh = TestLoggingHandler.create_fresh_handler()

    def teardown_method(self, method):
        # in case that a test changed the dirs
        self.reset_yl_assistants_dirs()

    def reset_yl_assistants_dirs(self):
        self.yl.assistants_dirs = [os.path.join(os.path.dirname(__file__), 'fixtures', 'assistants')]
        self.yl._classes = []

    def load_yaml_from_fixture(self, fixture):
        fixture_path = os.path.join(self.yl.assistants_dirs[0], '{0}.yaml'.format(fixture))
        fhandler = open(fixture_path)
        return yaml.load(fhandler)

    def test_assistant_from_yaml(self):
        y = self.load_yaml_from_fixture('c')
        a = self.yl.assistant_from_yaml('foo', y)

        assert a.name == 'c'
        assert a.fullname == 'C Language Tool'
        assert a.description == 'C Language Tool description...'
        assert a.role == 'creator'
        assert len(a.args) == 1
        assert a._dependencies == [{'default': [{'rpm': ['rpm']}]}]
        assert a._files == {
            'clientc': {'source': 'templates/c/client.c'},
            'serverc': {'source': 'templates/c/server.c'}
        }
        assert a._subassistant_names == ['d', 'e']
        assert a._run == [{'cl': 'ls foo/bar'}]

    def test_get_all_assistants_loads_all(self):
        # ass is a really nice variable name, isn't it?
        ass = YamlAssistantLoader.get_all_assistants()
        assert len(ass) == 4
        assert set(['c', 'd', 'e', 'f']) == set(map(lambda x: x.name, ass))

    def test_get_all_classes_sets_get_subassistants_properly(self):
        ass = YamlAssistantLoader.get_all_assistants()
        for a in ass:
            if a.name == 'c':
                assert set(map(lambda x: x.name, a.get_subassistants())) == set(['d', 'e'])
            else:
                assert a.get_subassistants() == []

    def test_get_top_level_assistants(self):
        ass = YamlAssistantLoader.get_top_level_assistants()
        assert set(['c', 'f']) == set(map(lambda x: x.name, ass))

    def test_assistant_from_yaml_doesnt_fail_on_missing_snippet(self):
        self.yl.assistants_dirs = [os.path.join(os.path.dirname(__file__),
                                                'fixtures',
                                                'assistants_with_snippet_problems')]
        y = self.load_yaml_from_fixture('no_snippet_for_arg')
        klass = self.yl.assistant_from_yaml('foo', y)
        assert ('WARNING', 'Couldn\'t expand argument bar in assistant no_snippet_for_arg: no such snippet: doesnt_exist') in self.tlh.msgs

    def test_assistant_from_yaml_doesnt_fail_on_missing_arg(self):
        self.yl.assistants_dirs = [os.path.join(os.path.dirname(__file__),
                                                'fixtures',
                                                'assistants_with_snippet_problems')]
        y = self.load_yaml_from_fixture('no_arg_in_snippet')
        a = self.yl.assistant_from_yaml('foo', y)
        assert ('WARNING', 'Couldn\'t find argument bar in snippet common_args wanted by assistant no_arg_in_snippet.') in self.tlh.msgs
