import os

import yaml
try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

import devassistant

from devassistant import settings
from devassistant import yaml_checker
from devassistant import yaml_loader
from devassistant import yaml_snippet_loader


class Cache(object):
    """Representation of DevAssistant cache file.
    Cache is stored in yaml file between devassistant invocations. Once it is loaded,
    it has following structure:

    # type of assistants
    {'crt':
        # a single cached assistant
        {'c':
            # attributes of this assistant needed to compose cli/gui
            {'attrs':
                # args of this assistant (if snippet is used, they're stored expanded)
                {'args':
                    {'foo': {'flags': ['-f', '--foo'],
                             'help': 'Help for foo parameter.'}},
                 'description': 'C Language Tool description...',
                 'fullname': 'C Language Tool'},
            # snippets that this assistant depends on with their last seen ctimes
            'snippets': {'somesnip': 11111111111},
            # last seen ctime of this assistant
            'ctime': 111111111111,
            # source file of this assistant
            'source': '/foo/bar/assistants/crt/c.yaml',
            # hierarchy of subassistants of this assistant
            'subhierarchy': {'d': {...}},
     'twk': {...},
     'prep': {...},
     'extra': {...},
     # version of devassistant that cache has been created with
     'version': devassistant.__version__}
    """

    def __init__(self, cache_file=settings.CACHE_FILE):
        """Inits a cache objects with given cache_file. Creates the cache file if
        it doesn't exist. If cache_file exists, but was created with different
        DevAssistant version, it gets deleted.

        Args:
            cache_file: cache file to use
        """
        self.cache_file = cache_file
        # snippets are shared across many assistants, so we remember their ctimes
        # here, because doing it again for each assistant would be very costly
        self.snip_ctimes = {}
        reset_cache = False
        if os.path.exists(self.cache_file):
            self.cache = yaml_loader.YamlLoader.load_yaml_by_path(cache_file) or {}
            if self.cache.get('version', '0.0.0') != devassistant.__version__:
                reset_cache = True
        else:
            if not os.path.exists(os.path.dirname(cache_file)):
                os.makedirs(os.path.dirname(cache_file))
            reset_cache = True

        # if writing the file raises, YamlAssistantLoader catches the exception
        #  and doesn't use cache at all
        if reset_cache:
            f = open(cache_file, 'w')
            self.cache = {'version': devassistant.__version__}
            f.close()

    def refresh_role(self, role, file_hierarchy):
        """Checks and refreshes (if needed) all assistants with given role.

        Args:
            role: role of assistants to refresh
            file_hierarchy: hierarchy as returned by devassistant.yaml_assistant_loader.\
                            YamlAssistantLoader.get_assistants_file_hierarchy
        """
        if role not in self.cache:
            self.cache[role] = {}
        was_change = self._refresh_hierarchy_recursive(self.cache[role], file_hierarchy)
        if was_change:
            cf = open(self.cache_file, 'w')
            yaml.dump(self.cache, cf, Dumper=Dumper)
            cf.close()

    def _refresh_hierarchy_recursive(self, cached_hierarchy, file_hierarchy):
        """Recursively goes through given corresponding hierarchies from cache and filesystem
        and adds/refreshes/removes added/changed/removed assistants.

        Args:
            cached_hierarchy: the respective hierarchy part from current cache
                              (for format see Cache class docstring)
            file_hierarchy: the respective hierarchy part from filesystem
                            (for format see what refresh_role accepts)

        Returns:
            True if self.cache has been changed, False otherwise (doesn't write anything
            to cache file)
        """
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
            was_change |= self._refresh_hierarchy_recursive(
                cached_hierarchy[ass]['subhierarchy'],
                file_hierarchy[ass]['subhierarchy'])

        return was_change

    def _ass_needs_refresh(self, cached_ass, file_ass):
        """Checks if assistant needs refresh.

        Assistant needs refresh iff any of following conditions is True:
        - stored source file is different than given source file
        - stored assistant ctime is lower than current source file ctime
        - stored list of subassistants is different than given list of subassistants
        - stored ctime of any of the snippets that this assistant uses to compose
          args is lower than current ctime of that snippet

        Args:
            cached_ass: an assistant from cache hierarchy
                        (for format see Cache class docstring)
            file_ass: the respective assistant from filesystem hierarchy
                      (for format see what refresh_role accepts)
        """
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
        """Completely refreshes cached assistant from file.

        Args:
            cached_ass: an assistant from cache hierarchy
                        (for format see Cache class docstring)
            file_ass: the respective assistant from filesystem hierarchy
                      (for format see what refresh_role accepts)
        """
        # we need to process assistant in custom way to see unexpanded args, etc.
        loaded_ass = yaml_loader.YamlLoader.load_yaml_by_path(file_ass['source'], log_debug=True)
        attrs = loaded_ass
        yaml_checker.check(file_ass['source'], attrs)
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
            if 'use' in argparams or 'snippet' in argparams:
                snippet_name = argparams.pop('use', None) or argparams.pop('snippet')
                snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(snippet_name)
                cached_ass['attrs']['args'][argname] = snippet.get_arg_by_name(argname)
                cached_ass['attrs']['args'][argname].update(argparams)
                cached_ass['snippets'][snippet.name] = self._get_snippet_ctime(snippet.name)
            else:
                cached_ass['attrs']['args'][argname] = argparams

    def _new_ass_hierarchy(self, file_ass):
        """Returns a completely new cache hierarchy for given assistant file.

        Args:
             file_ass: the assistant from filesystem hierarchy to create cache hierarchy for
                      (for format see what refresh_role accepts)
        Returns:
            the newly created cache hierarchy
        """
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
        """Returns and remembers (during this DevAssistant invocation) last ctime of given
        snippet.

        Calling ctime costs lost of time and some snippets, like common_args, are used widely,
        so we don't want to call ctime bazillion times on them during one invocation.

        Args:
            snip_name: name of snippet to get ctime for
        Returns:
            ctime of the snippet
        """
        if snip_name not in self.snip_ctimes:
            snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(snip_name)
            self.snip_ctimes[snip_name] = os.path.getctime(snippet.path)
        return self.snip_ctimes[snip_name]
