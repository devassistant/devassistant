import copy
import functools
import logging
import os

import six

from devassistant import argument
from devassistant import assistant_base
from devassistant import exceptions
from devassistant.logger import logger
from devassistant import lang
from devassistant import loaded_yaml
from devassistant import settings
from devassistant import utils
from devassistant import yaml_loader


def needs_fully_loaded(method):
    """Wraps all publicly callable methods of YamlAssistant. If the assistant was loaded
    from cache, this decorator will fully load it first time a publicly callable method
    is used.
    """
    @functools.wraps(method)
    def inner(self, *args, **kwargs):
        if not self.fully_loaded:
            loaded_yaml = yaml_loader.YamlLoader.load_yaml_by_path(self.path)
            self.parsed_yaml = loaded_yaml
            self.fully_loaded = True
        return method(self, *args, **kwargs)

    return inner


class YamlAssistant(assistant_base.AssistantBase, loaded_yaml.LoadedYaml):
    def __init__(self, name, parsed_yaml, path, superassistant, fully_loaded=True,
                 role=settings.DEFAULT_ASSISTANT_ROLE):
        self.name = name
        self.path = path
        self.superassistant = superassistant
        self.fully_loaded = fully_loaded
        self.role = role
        self.stop_flag = False
        self.parsed_yaml = parsed_yaml

    @property
    def parsed_yaml(self):
        return self._parsed_yaml

    @parsed_yaml.setter
    def parsed_yaml(self, value):
        # Use value.get(...) or <default> for all argument settings,
        # so that we are sure that <default> replaces "None" if needed
        # see: https://bugzilla.redhat.com/show_bug.cgi?id=1059305
        self._parsed_yaml = value

        # attributes needed for CLI/GUI - cached
        self.fullname = value.get('fullname') or self.name
        self.description = value.get('description') or ''
        self.args = self._construct_args(value.get('args') or {})
        self.icon_path = value.get('icon_path') or self.default_icon_path

        # attributes not needed for CLI/GUI - not cached
        self.files_dir = value.get('files_dir') or self.default_files_dir_for('assistants')
        self._files = value.get('files') or {}
        self._project_type = value.get('project_type') or []
        self._logging = value.get('logging') or []
        # set _run and _dependencies as empty in case assistant doesn't have them at all
        self._dependencies = value.get('dependencies') or []
        self._run = value.get('run') or []
        # handle more dependencies* and run* sections (except 'run' and 'dependencies'),
        # these two were already handled above
        for k, v in value.items():
            if k.startswith('run') or k.startswith('dependencies') and \
               k not in ['run', 'dependencies']:
                setattr(self, '_{0}'.format(k), v or [])
        self._pre_run = value.get('pre_run') or []
        self._post_run = value.get('post_run') or []

    @needs_fully_loaded
    def assert_fully_loaded(self):
        return True

    @property
    @needs_fully_loaded
    def project_type(self):
        pt = self._project_type
        if not pt:
            pt = [self.name]
            if self.superassistant:
                pt = self.superassistant.project_type + pt
        return pt

    @property
    def default_icon_path(self):
        """Returns default path to icon of this assistant.

        Assuming self.path == "/foo/assistants/crt/python/django.yaml"
        For image format in [png, svg]:
            1) Take the path of this assistant and strip it of load path
               (=> "crt/python/django.yaml")
            2) Substitute its extension for <image format>
               (=> "crt/python/django.<image format>")
            3) Prepend self.load_path + 'icons'
               (=> "/foo/icons/crt/python/django.<image format>")
            4) If file from 3) exists, return it
        Return empty string if no icon found.
        """
        supported_exts = ['.png', '.svg']
        stripped = self.path.replace(os.path.join(self.load_path, 'assistants'), '').strip(os.sep)
        for ext in supported_exts:
            icon_with_ext = os.path.splitext(stripped)[0] + ext
            icon_fullpath = os.path.join(self.load_path, 'icons', icon_with_ext)
            if os.path.exists(icon_fullpath):
                return icon_fullpath
        return ''

    def _construct_args(self, struct):
        args = []
        # Construct properly the iterable args from either a dict, or a list
        if isinstance(struct, dict):
            temp_args = struct.items()
        elif isinstance(struct, list):
            temp_args = [list(argdict.items())[0] for argdict in struct]
        else:
            raise TypeError('Args struct should be dict or list, is {0}'.format(type(struct)))

        for (arg_name, arg_params) in temp_args:
            try:
                args.append(argument.Argument.construct_arg(arg_name, arg_params))
            except exceptions.ExecutionException as e:
                msg = 'Problem when constructing argument {arg} in assistant {a}: {e}'.\
                    format(arg=arg_name, a=self.name, e=six.text_type(e))
                logger.warning(msg)
        return args

    def get_subassistants(self, use_cache=True):
        return self._subassistants

    @needs_fully_loaded
    def proper_kwargs(self, section, kwargs):
        """Returns kwargs updated with proper meta variables (like __assistant__).
        If this method is run repeatedly with the same section and the same kwargs,
        it always modifies kwargs in the same way.
        """
        kwargs['__section__'] = section
        kwargs['__assistant__'] = self
        kwargs['__env__'] = copy.deepcopy(os.environ)
        kwargs['__files__'] = [self._files]
        kwargs['__files_dir__'] = [self.files_dir]
        kwargs['__sourcefiles__'] = [self.path]
        # if any of the following fails, DA should keep running
        for i in ['system_name', 'system_version', 'distro_name', 'distro_version']:
            try:
                val = getattr(utils, 'get_' + i)()
            except:
                val = ''
            kwargs['__' + i + '__'] = val

    @needs_fully_loaded
    def logging(self, kwargs):
        # TODO: this doesn't seem to work, fix it...
        self.proper_kwargs('logging', kwargs)
        for l in self._logging:
            handler_type, l_list = l.popitem()
            if handler_type == 'file':
                level, lfile = l_list
                expanded_lfile = self._format(lfile, kwargs)
                # make dirs, create logger
                if not os.path.exists(os.path.dirname(expanded_lfile)):
                    os.makedirs(os.path.dirname(expanded_lfile))
                # add handler and formatter
                handler = logging.FileHandler(expanded_lfile, 'a+')
                formatter = logging.Formatter(
                    '%(asctime)-15s [%(event_type)] %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                handler.setLevel(getattr(logging, level.upper()))
                # register handler with the global logger
                logger.addHandler(handler)
            else:
                logger.warning('Unknown logger type {0}, ignoring.'.format(handler_type))

    @needs_fully_loaded
    def _get_dependency_sections_to_use(self, kwargs):
        sections = [getattr(self, '_dependencies', [])]
        if self.role == 'twk':
            proj_type = kwargs.get('project_type', [])
            # if project_type is "foo bar baz", then search for dependency sections
            # _dependencies_foo, _dependencies_foo_bar, _dependencies_foo_bar_baz
            for i in range(1, len(proj_type) + 1):
                possible_dep_section = '_dependencies_{0}'.format('_'.join(proj_type[:i]))
                if possible_dep_section in dir(self):
                    sections.append(getattr(self, possible_dep_section))
        # install these dependencies in any case
        for arg in kwargs:
            if '_dependencies_{0}'.format(arg) in dir(self):
                sections.append(getattr(self, '_dependencies_{0}'.format(arg)))

        return sections

    @needs_fully_loaded
    def dependencies(self, kwargs=None, expand_only=False):
        """Returns all dependencies of this assistant with regards to specified kwargs.

        If expand_only == False, this method returns list of mappings of dependency types
        to actual dependencies (keeps order, types can repeat), e.g.
        Example:
        [{'rpm', ['rubygems']}, {'gem', ['mygem']}, {'rpm', ['spam']}, ...]
        If expand_only == True, this method returns a structure that can be used as
        "dependencies" section and has all the "use: foo" commands expanded (but conditions
        are left untouched and variables are not substituted).
        """
        # we can't use {} as a default for kwargs, as that initializes the dict only once in Python
        # and uses the same dict in all subsequent calls of this method
        if not kwargs:
            kwargs = {}

        self.proper_kwargs('dependencies', kwargs)
        sections = self._get_dependency_sections_to_use(kwargs)
        deps = []

        for sect in sections:
            if expand_only:
                deps.extend(lang.expand_dependencies_section(sect, kwargs))
            else:
                deps.extend(lang.dependencies_section(sect, kwargs, runner=self))

        return deps

    @needs_fully_loaded
    def run(self, stage='', kwargs=None):
        # we can't use {} as a default for kwargs, as that initializes the dict only once in Python
        # and uses the same dict in all subsequent calls of this method
        if not kwargs:
            kwargs = {}

        self.proper_kwargs('run', kwargs)
        to_run = '_run'
        if stage:  # if we have stage, always use that
            to_run = '_' + stage + '_run'
        elif self.role == 'twk':
            # try to get a section to run from the most specialized one to the least
            # specialized one, e.g. first run_python_django, then run_python and then just run
            proj_type = kwargs.get('project_type', [])
            for i in range(len(proj_type), -1, -1):
                possible_run = '_'.join(['_run'] + proj_type[:i])
                if hasattr(self, possible_run):
                    to_run = possible_run
                    break

        return lang.run_section(getattr(self, to_run, {}), kwargs, runner=self)

    @needs_fully_loaded
    def stop(self):
        """ This function is used for stopping devassistant from GUI
        """
        self.stop_flag = True
