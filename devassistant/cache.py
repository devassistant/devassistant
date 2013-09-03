import os

import yaml
try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

from devassistant import settings
from devassistant import version
from devassistant import yaml_loader
from devassistant import yaml_snippet_loader

class Cache(object):
    def __init__(self, cache_file=settings.CACHE_FILE):
        self.cache_file = cache_file
        # snippets are shared across many assistants, so we remember their ctimes
        # here, because doing it again for each assistant would be very costly
        self.snip_ctimes = {}
        # TODO: try/catch creating the cache file, on failure don't use it
        reset_cache = False
        if os.path.exists(self.cache_file):
            self.cache = yaml_loader.YamlLoader.load_yaml_by_path(cache_file) or {}
            if self.cache.get('version', '0.0.0') != version.VERSION:
                reset_cache = True
        else:
            if not os.path.exists(os.path.dirname(cache_file)):
                os.makedirs(os.path.dirname(cache_file))
            reset_cache = True

        if reset_cache:
            f = open(cache_file, 'w')
            self.cache = {'version': version.VERSION}
            f.close()

    def refresh_role(self, role, file_hierarchy):
        if not role in self.cache:
            self.cache[role] = {}
        was_change = self._refresh_hierarchy_recursive(self.cache[role], file_hierarchy)
        if was_change:
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
            needs_refresh = False
            try:
                needs_refresh = self._ass_needs_refresh(cached_hierarchy[ass], file_hierarchy[ass])
            except:
                needs_refresh = True

            if needs_refresh:
                self._ass_refresh_attrs(cached_hierarchy[ass], file_hierarchy[ass])
                was_change = True
            was_change |= self._refresh_hierarchy_recursive(cached_hierarchy[ass]['subhierarchy'], file_hierarchy[ass]['subhierarchy'])

        return was_change


    def _ass_needs_refresh(self, cached_ass, file_ass):
        if cached_ass['source'] != file_ass['source']:
            return True
        if os.path.getctime(file_ass['source']) > cached_ass.get('ctime', 0.0):
            return True
        if set(cached_ass['subhierarchy'].keys()) != set(set(file_ass['subhierarchy'].keys())):
            return True
        for snip_name, snip_ctime in cached_ass['snippets'].items():
            if self._get_snippet_ctime(snip_name) > snip_ctime:
                return True

        return False

    def _ass_refresh_attrs(self, cached_ass, file_ass):
        # we need to process assistant in custom way to see unexpanded args, etc.
        loaded_ass = yaml_loader.YamlLoader.load_yaml_by_path(file_ass['source'])
        _, attrs = loaded_ass.popitem()
        cached_ass['source'] = file_ass['source']
        cached_ass['ctime'] = os.path.getctime(file_ass['source'])
        cached_ass['attrs'] = {}
        cached_ass['snippets'] = {}
        # only cache these attributes if they're actually found in assistant
        # we do this to specify the default values for them just in one place
        # which is currently YamlAssistant.parsed_yaml property setter
        for a in ['fullname', 'description', 'icon_path']:
            if a in attrs:
                cached_ass['attrs'][a] = attrs.get(a)
        # args have different processing, we can't just take them from assistant
        if 'args' in attrs:
            cached_ass['attrs']['args'] = {}
        for argname, argparams in attrs.get('args', {}).items():
            if 'snippet' in argparams:
                snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(argparams.pop('snippet'))
                cached_ass['attrs']['args'][argname] = snippet.get_arg_by_name(argname)
                cached_ass['attrs']['args'][argname].update(argparams)
                cached_ass['snippets'][snippet.name] = self._get_snippet_ctime(snippet.name)
            else:
                cached_ass['attrs']['args'][argname] = argparams

    def _new_ass_hierarchy(self, file_ass):
        ret_struct = {'source': '',
                      'subhierarchy': {},
                      'attrs': {},
                      'snippets': {}}
        ret_struct['source'] = file_ass['source']
        self._ass_refresh_attrs(ret_struct, file_ass)

        for name, subhierarchy in file_ass['subhierarchy'].items():
            ret_struct['subhierarchy'][name] = self._new_ass_hierarchy(subhierarchy)

        return ret_struct

    def _get_snippet_ctime(self, snip_name):
        if snip_name not in self.snip_ctimes:
            snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(snip_name)
            self.snip_ctimes[snip_name] = os.path.getctime(snippet.path)
        return self.snip_ctimes[snip_name]
