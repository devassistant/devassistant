import os

from devassistant import cache
from devassistant import exceptions
from devassistant.logger import logger
from devassistant import yaml_loader
from devassistant import settings
from devassistant import yaml_assistant
from devassistant import yaml_checker


class YamlAssistantLoader(object):
    assistants_dirs = list(map(lambda x: os.path.join(x, 'assistants'), settings.DATA_DIRECTORIES))

    @classmethod
    def get_assistants(cls, superassistants):
        """Returns list of assistants that are subassistants of given superassistants
        (I love this docstring).

        Args:
            roles: list of names of roles, defaults to all roles
        Returns:
            list of YamlAssistant instances with specified roles
        """
        _assistants = cls.load_all_assistants(superassistants)
        result = []
        for supa in superassistants:
            result.extend(_assistants[supa.name])

        return result

    @classmethod
    def load_all_assistants(cls, superassistants):
        """Fills self._assistants with loaded YamlAssistant instances of requested roles.

        Tries to use cache (updated/created if needed). If cache is unusable, it
        falls back to loading all assistants.

        Args:
            roles: list of required assistant roles
        """
        # mapping of assistant roles to lists of top-level assistant instances
        _assistants = {}
        # {'crt': CreatorAssistant, ...}
        superas_dict = dict(map(lambda a: (a.name, a), superassistants))
        to_load = set(superas_dict.keys())
        for tl in to_load:
            dirs = [os.path.join(d, tl) for d in cls.assistants_dirs]
            file_hierarchy = cls.get_assistants_file_hierarchy(dirs)
            # load all if we're not using cache or if we fail to load it
            load_all = not settings.USE_CACHE
            if settings.USE_CACHE:
                try:
                    cch = cache.Cache()
                    cch.refresh_role(tl, file_hierarchy)
                    _assistants[tl] = cls.get_assistants_from_cache_hierarchy(cch.cache[tl],
                                                                                  superas_dict[tl],
                                                                                  role=tl)
                except BaseException as e:
                    logger.debug('Failed to use DevAssistant cachefile {0}: {1}'.format(
                        settings.CACHE_FILE, e))
                    load_all = True
            if load_all:
                _assistants[tl] = cls.get_assistants_from_file_hierarchy(file_hierarchy,
                                                                             superas_dict[tl],
                                                                             role=tl)
        return _assistants

    @classmethod
    def get_assistants_from_cache_hierarchy(cls, cache_hierarchy, superassistant,
                                            role=settings.DEFAULT_ASSISTANT_ROLE):
        """Accepts cache_hierarch as described in devassistant.cache and returns
        instances of YamlAssistant (only with cached attributes) for loaded files

        Args:
            cache_hierarchy: structure as described in devassistant.cache
            role: role of all assistants in this hierarchy (we could find
                  this out dynamically but it's not worth the pain)
        Returns:
            list of top level assistants from given hierarchy; these assistants contain
            references to instances of their subassistants (and their subassistants, ...)
            Note, that the assistants are not fully loaded, but contain just cached attrs.
        """
        result = []

        for name, attrs in cache_hierarchy.items():
            ass = cls.assistant_from_yaml(attrs['source'],
                                          {name: attrs['attrs']},
                                          superassistant,
                                          fully_loaded=False,
                                          role=role)
            ass._subassistants = cls.get_assistants_from_cache_hierarchy(attrs['subhierarchy'],
                                                                         ass,
                                                                         role=role)
            result.append(ass)

        return result

    @classmethod
    def get_assistants_from_file_hierarchy(cls, file_hierarchy, superassistant,
                                           role=settings.DEFAULT_ASSISTANT_ROLE):
        """Accepts file_hierarch as returned by cls.get_assistant_file_hierarchy and returns
        instances of YamlAssistant for loaded files

        Args:
            file_hierarchy: structure as described in cls.get_assistants_file_hierarchy
            role: role of all assistants in this hierarchy (we could find
                  this out dynamically but it's not worth the pain)
        Returns:
            list of top level assistants from given hierarchy; these assistants contain
            references to instances of their subassistants (and their subassistants, ...)
        """
        result = []
        warn_msg = 'Failed to load assistant {source}, skipping subassistants.'

        for name, attrs in file_hierarchy.items():
            loaded_yaml = yaml_loader.YamlLoader.load_yaml_by_path(attrs['source'])
            if loaded_yaml is None:  # there was an error parsing yaml
                logger.warning(warn_msg.format(source=attrs['source']))
                continue
            try:
                ass = cls.assistant_from_yaml(attrs['source'],
                                              loaded_yaml,
                                              superassistant,
                                              role=role)
            except exceptions.YamlError as e:
                logger.warning(e)
                continue
            ass._subassistants = cls.get_assistants_from_file_hierarchy(attrs['subhierarchy'],
                                                                        ass,
                                                                        role=role)
            result.append(ass)

        return result

    @classmethod
    def get_assistants_file_hierarchy(cls, dirs):
        """Returns assistants file hierarchy structure (see below) representing assistant
        hierarchy in given directories.

        It works like this:
        1. It goes through all *.yaml files in all given directories and adds them into
           hierarchy (if there are two files with same name in more directories, the file
           from first directory wins).
        2. For each {name}.yaml file, it calls itself recursively for {name} subdirectories
           of all given directories.

        Args:
            dirs: directories to search
        Returns:
            hierarchy structure that looks like this:
            {'assistant1':
                {'source': '/path/to/assistant1.yaml',
                 'subhierarchy': {<hierarchy of subassistants>}},
             'assistant2':
                {'source': '/path/to/assistant2.yaml',
                 'subhierarchy': {<another hierarchy of subassistants}}
            }
        """
        result = {}
        for d in filter(lambda d: os.path.exists(d), dirs):
            for f in filter(lambda f: f.endswith('.yaml'), os.listdir(d)):
                assistant_name = f[:-5]
                if assistant_name not in result:
                    subas_dirs = [os.path.join(dr, assistant_name) for dr in dirs]
                    result[assistant_name] = {'source': os.path.join(d, f),
                                              'subhierarchy':
                                              cls.get_assistants_file_hierarchy(subas_dirs)}

        return result

    @classmethod
    def assistant_from_yaml(cls, source, y, superassistant, fully_loaded=True,
                            role=settings.DEFAULT_ASSISTANT_ROLE):
        """Constructs instance of YamlAssistant loaded from given structure y, loaded
        from source file source.

        Args:
            source: path to assistant source file
            y: loaded yaml structure
            superassistant: superassistant of this assistant
        Returns:
            YamlAssistant instance constructed from y with source file source
        Raises:
            YamlError: if the assistant is malformed
        """
        # In pre-0.9.0, we required assistant to be a mapping of {name: assistant_attributes}
        # now we allow that, but we also allow omitting the assistant name and putting
        # the attributes to top_level, too.
        name = os.path.splitext(os.path.basename(source))[0]
        yaml_checker.check(source, y)
        assistant = yaml_assistant.YamlAssistant(name, y, source, superassistant,
            fully_loaded=fully_loaded, role=role)

        return assistant
