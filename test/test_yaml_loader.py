import os

from devassistant.yaml_loader import YamlLoader

from test.logger import TestLoggingHandler

class TestYamlLoader(object):
    bad_syntax = os.path.join(os.path.dirname(__file__),
                              'fixtures',
                              'assistants_malformed',
                              'crt',
                              'a1.yaml')

    def setup_method(self, method):
        self.tlh = TestLoggingHandler.create_fresh_handler()

    def test_load_yaml_by_path_logs_and_returns_None_on_bad_syntax(self):
        e = 'Yaml error in {s} (line 0, column 3): mapping values are not allowed in this context'.\
                format(s=self.bad_syntax)
        assert YamlLoader.load_yaml_by_path(self.bad_syntax) == None
        assert ('WARNING', e) in self.tlh.msgs
