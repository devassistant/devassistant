import os

import pytest

from devassistant.yaml_snippet_loader import YamlSnippetLoader

class TestYamlSnippetLoader(object):
    def setup_method(self, method):
        self.yl = YamlSnippetLoader
        self.reset_yl_snippets_dirs()

    def teardown_method(self, method):
        self.reset_yl_snippets_dirs()

    def reset_yl_snippets_dirs(self):
        self.yl.snippets_dirs = [os.path.join(os.path.dirname(__file__), 'fixtures', 'snippets')]
        self.yl._snippets = {}

    def test_get_snippet_by_name(self):
        s = self.yl.get_snippet_by_name('snippet2')
        assert s.name == 'snippet2'
        assert s.get_run_section() == [{'log_i': 'this is snippet2!'}]
