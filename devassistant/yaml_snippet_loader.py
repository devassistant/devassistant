import os

from devassistant import exceptions
from devassistant import yaml_loader
from devassistant import settings
from devassistant.assistants import snippet

class YamlSnippetLoader(object):
    snippets_dirs = list(map(lambda x: os.path.join(x, 'snippets'), settings.DATA_DIRECTORIES))
    _snippets = {}

    @classmethod
    def _find_snippet(cls, name):
        for path, snippet in cls._snippets.items():
            if path.endswith(name + '.yaml'): return snippet

        return None

    @classmethod
    def get_snippet_by_name(cls, name):
        found = cls._find_snippet(name)
        if found != None:
            return found
        struct_dict = yaml_loader.YamlLoader.load_yaml(cls.snippets_dirs, name)
        if struct_dict != {}:
            path, parsed_yaml = struct_dict.popitem()
            snip = snippet.Snippet(path,
                                   parsed_yaml,
                                   template_dir=yaml_loader.YamlLoader._default_template_dir_for(path))
            cls._snippets[snip.path] = snip
            return snip

        raise exceptions.SnippetNotFoundException('no such snippet: {name}'.format(name=name))
