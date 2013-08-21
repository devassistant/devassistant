import os

import yaml
try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

from devassistant import settings
from devassistant import yaml_loader
from devassistant import yaml_snippet_loader

class Cache(object):
    def __init__(self, loader, cache_file=settings.CACHE_FILE):
        self.loader = loader
        self.cache_file = cache_file
        # TODO: try/catch creating the cache file, on failure don't use it
        # TODO: version cache?
        if not os.path.exists(cache_file):
            if not os.path.exists(os.path.dirname(cache_file)):
                os.makedirs(os.path.dirname(cache_file))
            open(cache_file, 'w').close()
        self.cache = yaml_loader.YamlLoader.load_yaml_by_path(cache_file) or {}

    def refresh_role(self, role, file_hierarchy):
        if not role in self.cache:
            self.cache[role] = {}
        self._refresh_hierarchy_recursive(self.cache[role], file_hierarchy)
        cf = open(self.cache_file, 'w')
        yaml.dump(self.cache, cf, Dumper=Dumper)
        cf.close()

    def _refresh_hierarchy_recursive(self, cached_hierarchy, file_hierarchy):
        was_change = False
        cached_ass = set(cached_hierarchy.keys())
        new_ass = set(file_hierarchy.keys())

        to_add = new_ass - cached_ass
        to_remove = cached_ass - new_ass
        to_check = cached_ass - to_remove

        if to_add or to_remove:
            was_change = True

        for ass in to_add:
            cached_hierarchy[ass] = self._new_ass_hierarchy(file_hierarchy[ass])

        for ass in to_remove:
            del cached_hierarchy[ass]

        for ass in to_check:
            if self._ass_needs_refresh(cached_hierarchy[ass], file_hierarchy[ass]):
                self._ass_refresh_attrs(cached_hierarchy[ass], file_hierarchy[ass])
                was_change = True
            was_change |= self._refresh_hierarchy_recursive(cached_hierarchy[ass]['subhierarchy'], file_hierarchy[ass]['subhierarchy'])

        return was_change


    def _ass_needs_refresh(self, cached_ass, file_ass):
        if cached_ass['source'] != file_ass['source']:
            return True
        if os.path.getctime(file_ass['source']) > os.path.getctime(self.cache_file):
            return True
        if set(cached_ass['subhierarchy'].keys()) != set(set(file_ass['subhierarchy'].keys())):
            return True
        #TODO: snippet timestamps

        return False

    def _ass_refresh_attrs(self, cached_ass, file_ass):
        loaded_ass = self.loader.assistant_from_yaml(file_ass['source'], yaml_loader.YamlLoader.load_yaml_by_path(file_ass['source']))
        cached_ass['source'] = file_ass['source']
        #TODO: expand snippets in args properly
        cached_ass['attrs'] = {'fullname': loaded_ass.fullname,
                               'description': loaded_ass.description,
                               'args': loaded_ass.args}

    def _new_ass_hierarchy(self, file_ass):
        ret_struct = {'source': '',
                      'subhierarchy': {},
                      'attrs': {},
                      'snippets': {}}
        ret_struct['source'] = file_ass['source']
        loaded_ass = self.loader.assistant_from_yaml(ret_struct['source'], yaml_loader.YamlLoader.load_yaml_by_path(ret_struct['source']))
        self._ass_refresh_attrs(ret_struct, file_ass)
        # TODO: set snippets this assistant depends on
        for name, subhierarchy in file_ass['subhierarchy'].items():
            ret_struct['subhierarchy'][name] = self._new_ass_hierarchy(subhierarchy)
        return ret_struct
