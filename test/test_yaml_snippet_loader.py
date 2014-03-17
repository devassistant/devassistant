import os

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

    def test_get_snippet_with_dotted_name(self):
        s = self.yl.get_snippet_by_name('snippetd.subdir.snippet1')
        assert s.name == 'snippet1'
        assert s.get_dependencies_section() == [{'rpm': ['foo']}]

    def test_get_all_snippets(self):
        s = self.yl.get_all_snippets()
        assert len(s) == 3
        assert s['snippet1'][0] == {}
        assert s['snippet2'][0] == {}

        assert s['snippet1'][1].name == 'snippet1'
        assert s['snippet1'][1].get_run_section() == [{'log_i': 'this is snippet1!'}]

        assert s['snippet2'][1].name == 'snippet2'
        assert s['snippet2'][1].get_run_section() == [{'log_i': 'this is snippet2!'}]

        assert s['snippetd'][1] == None
        assert s['snippetd'][0]['subdir'][1] == None
        assert s['snippetd'][0]['subdir'][0]['snippet1'][1].name == 'snippet1'
        assert s['snippetd'][0]['subdir'][0]['snippet1'][1].get_dependencies_section() == \
                [{'rpm': ['foo']}]
