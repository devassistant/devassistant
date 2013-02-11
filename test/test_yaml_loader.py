import os

import pytest
import yaml

from devassistant.yaml_loader import YamlLoader

class TestYamlLoader(object):
    def setup_method(self, method):
        self.yl = YamlLoader
        self.yl.yaml_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

    def load_yaml_from_fixture(self, fixture):
        fixture_path = os.path.join(self.yl.yaml_dir, '{0}.yaml'.format(fixture))
        fhandler = open(fixture_path)
        return yaml.load(fhandler)

    def test_class_from_yaml(self):
        y = self.load_yaml_from_fixture('c')
        klass = self.yl.class_from_yaml(y)
        
        assert klass.name == 'c'
        assert klass.fullname == 'C Language Tool'
        assert len(klass.args) == 1
        assert klass._dependencies == {'rpm': ['rpm']}
        assert klass._fail_if == [{'cl': 'ls /'}]
        assert klass._files == {
            'clientc': {'source': 'templates/c/client.c'},
            'serverc': {'source': 'templates/c/server.c'}
        }
        assert klass._subassistants == ['d', 'e']
        assert klass._run == [{'cl': 'ls foo/bar'}]

    def test_get_all_classes_loads_all(self):
        clss = YamlLoader.get_all_classes()
        assert len(clss) == 4
        assert set(['c', 'd', 'e', 'f']) == set(map(lambda x: x.name, clss))

    def test_get_all_classes_sets_get_subassistants_properly(self):
        clss = YamlLoader.get_all_classes()
        for kls in clss:
            if kls.name == 'c':
                assert set(map(lambda x: x.name, kls().get_subassistants())) == set(['d', 'e'])
            else:
                assert kls().get_subassistants() == []

    def test_get_top_level_assistants(self):
        clss = YamlLoader.get_top_level_assistants()
        assert set(['c', 'f']) == set(map(lambda x: x.name, clss))
