import os

from devassistant import exceptions
from devassistant import yaml_loader
from devassistant import settings
from devassistant import snippet
from devassistant import yaml_checker


class YamlSnippetLoader(object):
    snippets_dirs = list(map(lambda x: os.path.join(x, 'snippets'), settings.DATA_DIRECTORIES))

    @classmethod
    def _create_snippet(cls, name, path, parsed_yaml):
        yaml_checker.check(path, parsed_yaml)
        snip = snippet.Snippet(name,
                               parsed_yaml,
                               path)

        return snip

    @classmethod
    def get_snippet_by_name(cls, name):
        """name is in dotted format, e.g. topsnippet.something.wantedsnippet"""
        name_with_dir_separators = name.replace('.', os.path.sep)
        loaded = yaml_loader.YamlLoader.load_yaml_by_relpath(cls.snippets_dirs,
                                                             name_with_dir_separators + '.yaml')
        if loaded:
            return cls._create_snippet(name, *loaded)

        raise exceptions.SnippetNotFoundException('no such snippet: {name}'.
                                                  format(name=name_with_dir_separators))

    @classmethod
    def get_all_snippets(cls):
        # maps dotted snippet names to Snippet objects, e.g. {'foo.bar': <Snippet object>, ...}
        _snippets = {}
        for d in cls.snippets_dirs:
            loaded = yaml_loader.YamlLoader.load_all_yamls([d])
            for path, parsed_yaml in loaded.items():
                name = path[len(d):].strip(os.path.sep)
                name = os.path.splitext(name)[0].replace(os.path.sep, '.')
                # override even if the snippet is already there - we need to make
                # sure that we prefer snippets from the last load path
                _snippets[name] = cls._create_snippet(name, path, parsed_yaml)
        return _snippets
