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
        assert klass._invoke_if_subassistant_used == False
        assert klass._dependencies == {'rpm': ['rpm']}
        assert klass._fail_if == [{'cl': 'ls /'}]
        assert klass._files == {
            'clientc': {'source': 'templates/c/client.c'},
            'serverc': {'source': 'templates/c/server.c'}
        }
        assert klass._subassistants == ['d', 'e']
        assert klass._run == [{'cl': 'ls foo/bar'}]
