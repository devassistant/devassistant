import functools
import logging
import os

from devassistant import argument
from devassistant import assistant_base
from devassistant import command
from devassistant import exceptions
from devassistant.logger import logger
from devassistant import lang
from devassistant import loaded_yaml
from devassistant import yaml_loader
from devassistant import yaml_snippet_loader

def needs_fully_loaded(method):
    """Wraps all publicly callable methods of YamlAssistant. If the assistant was loaded
    from cache, this decorator will fully load it first time a publicly callable method
    is used.
    """
    @functools.wraps(method)
    def inner(self, *args, **kwargs):
        if not self.fully_loaded:
            self.parsed_yaml = yaml_loader.YamlLoader.load_yaml_by_path(self.path).popitem()[1]
            self.fully_loaded = True
        return method(self, *args, **kwargs)

    return inner

class YamlAssistant(assistant_base.AssistantBase, loaded_yaml.LoadedYaml):
    def __init__(self, name, parsed_yaml, path, fully_loaded=True, role='crt'):
        self.name = name
        self.path = path
        self.fully_loaded = fully_loaded
        self.role = role
        self.stop_flag = False
        self.parsed_yaml = parsed_yaml

    @property
    def parsed_yaml(self):
        return self._parsed_yaml

    @parsed_yaml.setter
    def parsed_yaml(self, value):
        self._parsed_yaml = value

        # attributes needed for CLI/GUI - cached
        self.fullname = value.get('fullname', self.name)
        self.description = value.get('description', '')
        self.args = self._construct_args(value.get('args', {}))
        self.icon_path = value.get('icon_path', self.default_icon_path)

        # attributes not needed for CLI/GUI - not cached
        self.files_dir = value.get('files_dir', self.default_files_dir_for('assistants'))
        self._files = value.get('files', {})
        self._logging = value.get('logging', [])
        # modifiers use this to decide whether or not to read .devassistant
        self._devassistant_projects_only = value.get('devassistant_projects_only', True)
        # set _run and _dependencies as empty in case assistant doesn't have them at all
        self._dependencies = value.get('dependencies', [])
        self._run = value.get('run', [])
        # handle more dependencies* and run* sections
        for k, v in value.items():
            if k.startswith('run') or k.startswith('dependencies'):
                setattr(self, '_{0}'.format(k), v)
        self._pre_run = value.get('pre_run', [])
        self._post_run = value.get('post_run', [])

    @needs_fully_loaded
    def assert_fully_loaded(self):
        return True

    @property
    def default_icon_path(self):
        """Returns default path to icon of this assistant.

        Assuming self.path == "/foo/assistants/crt/python/django.yaml"
        1) Take the path of this assistant and strip it of load path
           (=> "crt/python/django.yaml")
        2) Substitute its extension for ".svg"
           (=> "crt/python/django.svg")
        3) Prepend self.load_path + 'icons'
           (=> "/foo/icons/crt/python/django.scg")
        """
        stripped = self.path.replace(os.path.join(self.load_path, 'assistants'), '').strip(os.sep)
        new_ext = os.path.splitext(stripped)[0] + '.svg'
        return os.path.join(self.load_path, 'icons', new_ext)

    def _construct_args(self, struct):
        args = []
        for arg_name, arg_params in struct.items():
            use_snippet = arg_params.pop('snippet', None)
            if use_snippet:
                # if snippet is used, take this parameter from snippet and update
                # it with current arg_params, if any
                try:
                    problem = None
                    snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(use_snippet)
                    arg_params = dict(snippet.args.pop(arg_name), **arg_params)
                except exceptions.SnippetNotFoundException as e:
                    problem = 'Couldn\'t expand argument {arg} in assistant {a}: ' + str(e)
                except KeyError as e: # snippet doesn't have the requested argument
                    problem = 'Couldn\'t find argument {arg} in snippet {snip} wanted by assistant {a}.'

                if problem:
                    logger.warning(problem.format(snip=use_snippet,
                                                  arg=arg_name,
                                                  a=self.name))
                    continue

                # this works much like snippet.args.pop(arg_name).update(arg_params),
                # but unlike it, this actually returns the updated dict

            arg = argument.Argument(arg_name, *arg_params.pop('flags'), **arg_params)
            args.append(arg)
        return args

    def get_subassistants(self):
        return self._subassistants

    @needs_fully_loaded
    def proper_kwargs(self, section='run', **kwargs):
        """Returns kwargs updated with proper meta variables (like __assistant__), and possibly
        updated with values from .devassistant file, when appropriate."""
        if self.role == 'mod' and self._devassistant_projects_only:
            # don't rewrite old values
            # first get the new ones and then update them with the old
            new_kwargs = command.Command('dda_r', kwargs.get('path', '.'), kwargs).run()
            new_kwargs.update(kwargs)
            kwargs = new_kwargs
        kwargs['__section__'] = section
        kwargs['__assistant__'] = self
        kwargs['__files__'] = [self._files]
        kwargs['__files_dir__'] = [self.files_dir]
        kwargs['__scls__'] = []
        return kwargs

    @needs_fully_loaded
    def logging(self, **kwargs):
        kwargs = self.proper_kwargs(section='logging', **kwargs)
        for l in self._logging:
            handler_type, l_list = l.popitem()
            if handler_type == 'file':
                level, lfile = l_list
                expanded_lfile = self._format(lfile, **kwargs)
                # make dirs, create logger
                if not os.path.exists(os.path.dirname(expanded_lfile)):
                    os.makedirs(os.path.dirname(expanded_lfile))
                # add handler and formatter
                handler = logging.FileHandler(expanded_lfile, 'a+')
                formatter = logging.Formatter('%(asctime)-15s [%(event_type)] %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                handler.setLevel(getattr(logging, level.upper()))
                # register handler with the global logger
                logger.addHandler(handler)
            else:
                logger.warning('Unknown logger type {0}, ignoring.'.format(handler_type))

    @needs_fully_loaded
    def dependencies(self, **kwargs):
        """Returns all dependencies of this assistant with regards to specified kwargs.

        This is list of mappings of dependency types to actual dependencies
        (keeps order, types can repeat), e.g.
        Example:
        [{'rpm', ['rubygems']}, {'gem', ['mygem']}, {'rpm', ['spam']}, ...]
        """

        kwargs = self.proper_kwargs(section='dependencies', **kwargs)
        sections = [getattr(self, '_dependencies', [])]
        if self.role == 'mod' and self._devassistant_projects_only:
            # if subassistant_path is "foo bar baz", then search for dependency sections
            # _dependencies_foo, _dependencies_foo_bar, _dependencies_foo_bar_baz
            for i in range(1, len(kwargs.get('subassistant_path', [])) + 1):
                possible_dep_section = '_dependencies_{0}'.format('_'.join(kwargs['subassistant_path'][:i]))
                if possible_dep_section in dir(self):
                    sections.append(getattr(self, possible_dep_section))
        # install these dependencies in any case
        for arg in kwargs:
            if '_dependencies_{0}'.format(arg) in dir(self):
                sections.append(getattr(self, '_dependencies_{0}'.format(arg)))

        deps = []

        for sect in sections:
            deps.extend(lang.dependencies_section(sect, kwargs, runner=self))

        return deps

    def _get_section_to_run(self, section, **kwargs):
        """Returns the proper section to run.
        Args:
            section: name of section to run
            **kwargs: devassistant arguments
        Returns:
            section to run - dict, None if not found
        """
        to_run = None

        if section:
            underscored = '_' + section
            if underscored in dir(self):
                to_run = getattr(self, underscored)

        return to_run

    @needs_fully_loaded
    def run(self, **kwargs):
        kwargs = self.proper_kwargs(section='run', **kwargs)
        if self.role == 'mod' and self._devassistant_projects_only:
            # try to get a section to run from the most specialized one to the least specialized one
            # e.g. first run_python_django, then run_python and then just run
            sa_path = kwargs.get('subassistant_path', [])
            for i in range(len(sa_path), -1, -1):
                path = '_'.join(sa_path[:i])
                if path:
                    path = '_' + path
                to_run = self._get_section_to_run(section='run{path}'.format(path=path), **kwargs)
                if to_run:
                    break
        else:
            to_run = self._get_section_to_run(section='run', **kwargs)

        if self._pre_run:
            lang.run_section(self._pre_run, kwargs, runner=self)
        lang.run_section(to_run, kwargs, runner=self)
        if self._post_run:
            lang.run_section(self._post_run, kwargs, runner=self)

    @needs_fully_loaded
    def stop(self):
        """ This function is used for stopping devassistant from GUI
        """
        self.stop_flag = True
