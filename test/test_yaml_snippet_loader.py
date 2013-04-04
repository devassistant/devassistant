import os

import pytest

from devassistant.yaml_snippet_loader import YamlSnippetLoader

class TestYamlSnippetLoader(object):
    def setup_method(self, method):
        self.yl = YamlSnippetLoader
        self.yl.snippets_dirs = [os.path.join(os.path.dirname(__file__), 'fixtures', 'snippets')]

    def test_get_all_snippets(self):
        # TODO: testing getting the run section should have its own test class
        # this should rather test the loading itself
        s = self.yl.get_all_snippets()
        assert len(s) == 2
        assert set(map(lambda x: x.name, s)) == set(['snippet1', 'snippet2'])
        assert [{'log_i': 'this is snippet1!'}] in map(lambda x: x.get_run_section(), s)
        assert [{'log_i': 'this is snippet2!'}] in map(lambda x: x.get_run_section(), s)

    def test_get_snippet_by_name(self):
        s = self.yl.get_snippet_by_name('snippet2')
        assert s.name == 'snippet2'
        assert s.get_run_section() == [{'log_i': 'this is snippet2!'}]
