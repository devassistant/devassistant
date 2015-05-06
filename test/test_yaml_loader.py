import os
import re

import pytest

from devassistant.yaml_loader import YamlLoader

from test.logger import LoggingHandler

class TestYamlLoader(object):
    bad_syntax = os.path.join(os.path.dirname(__file__),
                              'fixtures',
                              'assistants_malformed',
                              'crt')
    bad_syntax1 = os.path.join(bad_syntax, 'a1.yaml')
    bad_syntax3 = os.path.join(bad_syntax, 'a3.yaml')

    def setup_method(self, method):
        self.tlh = LoggingHandler.create_fresh_handler()

    @pytest.mark.parametrize('which_bad, err', [
        ('bad_syntax1', 'Yaml error in {p} \(line 0, column 3\): mapping values are ' + \
                        'not allowed (in this context|here)'),
        ('bad_syntax3', 'Yaml error in {p} \(line 2, column 0\): (did not find expected ' + \
                        'key|expected <block end>, but found \'-\')'),
    ])
    def test_load_yaml_by_path_logs_and_returns_None_on_bad_syntax(self, which_bad, err):
        path = getattr(self, which_bad)
        e = err.format(p=path)
        assert YamlLoader.load_yaml_by_path(path) == None
        assert 'WARNING' == self.tlh.msgs[0][0]
        assert re.match(e, self.tlh.msgs[0][1])
