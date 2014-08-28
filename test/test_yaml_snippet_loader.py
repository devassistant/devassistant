import os
import pytest

from devassistant import exceptions
from devassistant.yaml_snippet_loader import YamlSnippetLoader

class TestYamlSnippetLoader(object):
    def setup_method(self, method):
        self.yl = YamlSnippetLoader
        self.reset_yl_snippets_dirs()

    def teardown_method(self, method):
        self.reset_yl_snippets_dirs()

    def reset_yl_snippets_dirs(self, directory='snippets'):
        self.yl.snippets_dirs = [os.path.join(os.path.dirname(__file__), 'fixtures', directory)]
        self.yl._snippets = {}

    def test_get_snippet_by_name(self):
        s = self.yl.get_snippet_by_name('snippet2')
        assert s.name == 'snippet2'
        assert s.get_run_section() == [{'log_i': 'this is snippet2!'}]

    def test_get_snippet_with_dotted_name(self):
        s = self.yl.get_snippet_by_name('snippetd.subdir.snippet1')
        assert s.name == 'snippet1'
        assert s.get_dependencies_section() == [{'rpm': ['foo']}]

    def test_get_all_snippets(self):
        s = self.yl.get_all_snippets()

        assert len(s) == 3

        assert s['snippet1'].name == 'snippet1'
        assert s['snippet1'].get_run_section() == [{'log_i': 'this is snippet1!'}]

        assert s['snippet2'].name == 'snippet2'
        assert s['snippet2'].get_run_section() == [{'log_i': 'this is snippet2!'}]

        assert s['snippetd.subdir.snippet1'].name == 'snippet1'
        assert s['snippetd.subdir.snippet1'].get_dependencies_section() == [{'rpm': ['foo']}]

    @pytest.mark.parametrize(('snippet', 'error', 'err_str'), [
        ('snippet1', exceptions.YamlSyntaxError, 'Invalid section name: section'),
    ])
    def test_get_malformed_snippet(self, snippet, error, err_str):
        self.reset_yl_snippets_dirs('snippets_malformed')
        with pytest.raises(error) as excinfo:
            self.yl.get_snippet_by_name(snippet)
        assert err_str in str(excinfo.value)

