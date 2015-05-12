import os

import pytest
import yaml

from devassistant.assistant_base import AssistantBase
from devassistant import exceptions
from devassistant import settings
from devassistant.yaml_assistant_loader import YamlAssistantLoader

from test.logger import LoggingHandler

class CreatorAssistant(AssistantBase):
    name = 'crt'

class TestYamlAssistantLoader(object):
    def setup_method(self, method):
        self.yl = YamlAssistantLoader
        self.reset_yl_assistants_dirs()
        self.yl._assistants = {}
        self.tlh = LoggingHandler.create_fresh_handler()

    def teardown_method(self, method):
        # in case that a test changed the dirs
        self.reset_yl_assistants_dirs()
        settings.USE_CACHE = True

    def reset_yl_assistants_dirs(self):
        self.yl.assistants_dirs = [os.path.join(os.path.dirname(__file__), 'fixtures', 'assistants')]
        self.yl._classes = []

    def load_yaml_from_fixture(self, fixture):
        fixture_path = os.path.join(self.yl.assistants_dirs[0], 'crt', '{0}.yaml'.format(fixture))
        fhandler = open(fixture_path)
        return yaml.load(fhandler)

    def test_assistant_from_yaml(self):
        # TODO: probably move testing to yaml_assistants tests, since
        # most of this stuff is done there now (although it's testable here)
        y = self.load_yaml_from_fixture('c')
        a = self.yl.assistant_from_yaml('c.yaml', y, CreatorAssistant())

        assert a.name == 'c'
        assert a.fullname == 'C Language Tool'
        assert a.description == 'C Language Tool description...'
        assert a.role == 'crt'
        assert len(a.args) == 1
        assert a._dependencies == [{'default': [{'rpm': ['rpm']}]}]
        assert a._files == {
            'clientc': {'source': 'crt/c/client.c'},
            'serverc': {'source': 'crt/c/server.c'}
        }
        assert a._run == [{'cl': 'ls foo/bar'}]

    def test_load_all_assistants_loads_proper_structure(self):
        assistants = YamlAssistantLoader.load_all_assistants(superassistants=[CreatorAssistant()])
        assert len(assistants) == 1
        assert len(assistants['crt']) == 2
        # ass is a really nice variable name, isn't it?
        a1 = assistants['crt'][0]
        a2 = assistants['crt'][1]
        if a1.name == 'c':
            c, f = a1, a2
        else:
            c, f = a2, a1
        assert len(c.get_subassistants()) == 2
        assert len(f.get_subassistants()) == 1
        #TODO: some more checks...

    def test_get_top_level_assistants(self):
        ass = YamlAssistantLoader.get_assistants(superassistants=[CreatorAssistant])
        assert set(['c', 'f']) == set(map(lambda x: x.name, ass))

    def test_assistant_from_yaml_doesnt_fail_on_missing_snippet(self):
        self.yl.assistants_dirs = [os.path.join(os.path.dirname(__file__),
                                                'fixtures',
                                                'assistants_with_snippet_problems')]
        y = self.load_yaml_from_fixture('no_snippet_for_arg')
        self.yl.assistant_from_yaml('no_snippet_for_arg.yaml', y, CreatorAssistant())
        assert ('WARNING',
                'Problem when constructing argument bar in assistant no_snippet_for_arg: ' + \
                'no such snippet: doesnt_exist') \
            in self.tlh.msgs

    def test_assistant_from_yaml_doesnt_fail_on_missing_arg(self):
        self.yl.assistants_dirs = [os.path.join(os.path.dirname(__file__),
                                                'fixtures',
                                                'assistants_with_snippet_problems')]
        y = self.load_yaml_from_fixture('no_arg_in_snippet')
        self.yl.assistant_from_yaml('no_arg_in_snippet.yaml', y, CreatorAssistant())
        assert ('WARNING',
                'Problem when constructing argument bar in assistant no_arg_in_snippet: ' + \
                'Couldn\'t find arg bar in snippet snippet1.') \
            in self.tlh.msgs

    def test_no_cache(self):
        settings.USE_CACHE = False
        oldm = self.yl.get_assistants_from_cache_hierarchy
        self.yl.get_assistants_from_cache_hierarchy = None
        # if YamlAssistantLoader tries to load from cache now, it will log debug message
        ass = self.yl.get_assistants(superassistants=[CreatorAssistant])
        assert self.tlh.msgs == []
        # assert that assistants were loaded ok
        assert set(['c', 'f']) == set(map(lambda x: x.name, ass))
        self.yl.get_assistants_from_cache_hierarchy = oldm

    def test_get_assistants_from_file_hierarchy_with_empty_assistant(self):
        empty = os.path.join(os.path.dirname(__file__),
                             'fixtures',
                             'empty.yaml')
        res = self.yl.get_assistants_from_file_hierarchy({'empty': {'source': empty,
                                                                    'subhierarchy': {}}},
                                                         None)
        assert len(res) == 1

    def test_get_assistants_from_file_hierarchy_with_bad_syntax(self):
        bad_syntax = os.path.join(os.path.dirname(__file__),
                                  'fixtures',
                                  'assistants_malformed',
                                  'crt',
                                  'a1.yaml')
        err = 'Failed to load assistant {src}, skipping subassistants.'.format(src=bad_syntax)
        self.yl.assistants_dirs = [os.path.join(os.path.split(bad_syntax[:-2]))]
        res = self.yl.get_assistants_from_file_hierarchy({'a1': {'source': bad_syntax,
                                                                 'subhierarchy': {}}},
                                                         None)
        assert ('WARNING', err) in self.tlh.msgs
        assert res == []

    def test_get_assistants_from_file_hierarchy_with_bad_assistant(self):
        bad_syntax = os.path.join(os.path.dirname(__file__),
                                  'fixtures',
                                  'assistants_malformed',
                                  'crt',
                                  'a2.yaml')
        err = 'In {src}:\nAssistants and snippets must be Yaml mappings, not "asd"!'.\
            format(src=bad_syntax)
        self.yl.assistants_dirs = [os.path.join(os.path.split(bad_syntax[:-2]))]
        res = self.yl.get_assistants_from_file_hierarchy({'a1': {'source': bad_syntax,
                                                                 'subhierarchy': {}}},
                                                         None)
        assert ('WARNING', err) in self.tlh.msgs
        assert res == []

    def test_assistant_from_yaml_raises_on_bad_assistant(self):
        with pytest.raises(exceptions.YamlError):
            self.yl.assistant_from_yaml('/foo/bar', 'not a mapping', None)
