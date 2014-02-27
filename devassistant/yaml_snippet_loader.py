import os

from devassistant import exceptions
from devassistant import yaml_loader
from devassistant import settings
from devassistant import snippet
from devassistant import yaml_checker


class YamlSnippetLoader(object):
    snippets_dirs = list(map(lambda x: os.path.join(x, 'snippets'), settings.DATA_DIRECTORIES))
    _snippets = {}

    @classmethod
    def _find_snippet(cls, name):
        for snip in cls._snippets.values():
            if snip.name == name:
                return snip

        return None

    @classmethod
    def get_snippet_by_name(cls, name):
        found = cls._find_snippet(name)
        if found is not None:
            return found
        loaded = yaml_loader.YamlLoader.load_yaml_by_relpath(cls.snippets_dirs, name + '.yaml')
        if loaded:
            path, parsed_yaml = loaded
            yaml_checker.check(path, parsed_yaml)
            snip = snippet.Snippet(name,
                                   parsed_yaml,
                                   path)
            cls._snippets[snip.path] = snip
            return snip

        raise exceptions.SnippetNotFoundException('no such snippet: {name}'.format(name=name))
