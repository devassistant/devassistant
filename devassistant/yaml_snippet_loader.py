import os

from devassistant import exceptions
from devassistant import yaml_loader
from devassistant import settings
from devassistant import snippet
from devassistant import yaml_checker


class YamlSnippetLoader(object):
    snippets_dirs = list(map(lambda x: os.path.join(x, 'snippets'), settings.DATA_DIRECTORIES))
    # format: {'snippet1': ({'subsnippet1': ({}, <Snippet object or None>)},
    #                        <Snippet object or None>), ...}
    _snippets = {}
    _loaded_all = False

    @classmethod
    def _find_snippet(cls, name):
        name_parts = name.split('.')
        searched_dict = cls._snippets
        found = None

        for i, np in enumerate(name_parts):
            if np in searched_dict:
                if i + 1 == len(name_parts):
                    found = searched_dict[np][1]
                else:
                    searched_dict = searched_dict[np][0]

        return found

    @classmethod
    def _create_snippet(cls, name, path, parsed_yaml):
        name_parts = name.split('.')
        yaml_checker.check(path, parsed_yaml)
        snip = snippet.Snippet(name,
                               parsed_yaml,
                               path)

        # store the new snippet in cls._snippets, optionally creating
        # the "path" to it
        curr_dict = cls._snippets
        for i, np in enumerate(name_parts):
            # construct "new_member" (the tuple in {'snip': ({}, <Snippet or None>)} of curr_dict
            # new_member[0] is the dict that's currently there (if any) or {}
            # new_member[1] is the snippet/None that's already there or the new snippet
            #  if we're at the end
            old_dct, old_snip = curr_dict.get(np, ({}, None))
            new_member = (old_dct,
                          snip if i + 1 == len(name_parts) else old_snip)
            curr_dict[np] = new_member
            curr_dict = curr_dict[np][0]

        return snip

    @classmethod
    def get_snippet_by_name(cls, name):
        """name is in dotted format, e.g. topsnippet.something.wantedsnippet"""
        found = cls._find_snippet(name)
        if found is not None:
            return found
        name_with_dir_separators = name.replace('.', os.path.sep)
        loaded = yaml_loader.YamlLoader.load_yaml_by_relpath(cls.snippets_dirs,
                                                             name_with_dir_separators + '.yaml')
        if loaded:
            return cls._create_snippet(name, *loaded)

        raise exceptions.SnippetNotFoundException('no such snippet: {name}'.\
                                                  format(name=name_with_dir_separators))

    @classmethod
    def get_all_snippets(cls):
        if not cls._loaded_all:
            for d in cls.snippets_dirs:
                loaded = yaml_loader.YamlLoader.load_all_yamls([d])
                for path, parsed_yaml in loaded.items():
                    name = path[len(d):].strip(os.path.sep)
                    name = os.path.splitext(name)[0].replace(os.path.sep, '.')
                    cls._create_snippet(name, path, parsed_yaml)
            cls._loaded_all = True
        return cls._snippets
