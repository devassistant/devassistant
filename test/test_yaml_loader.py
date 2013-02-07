import os
import pytest

from devassistant.yaml_loader import YamlLoader

class TestYamlLoader(object):
    def setup_method(self, method):
        self.yl = YamlLoader()
        yl.yaml_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
