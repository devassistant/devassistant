import os

from devassistant import yaml_loader
from devassistant.assistants import snippet

class YamlSnippetLoader(object):
    snippets_dirs = [os.path.join(os.path.dirname(__file__), 'assistants', 'snippets')]
    _snippets = []

    @classmethod
    def get_all_snippets(cls):
        # this in fact caches the snippets (if loaded already, doesn't load them again)
        if not cls._snippets:
            parsed_yamls = yaml_loader.YamlLoader.load_all_yamls(cls.snippets_dirs)

            for k, v in parsed_yamls.items():
                cls._snippets.append(snippet.Snippet(k, v))

        return cls._snippets

    @classmethod
    def get_snippet_by_name(cls, name):
        for s in cls.get_all_snippets():
            if s.name == name:
                return s
