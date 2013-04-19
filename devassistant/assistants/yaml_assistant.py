import copy
import logging
import os

from devassistant import assistant_base
from devassistant import exceptions
from devassistant.assistants.command_formatter import CommandFormatter
from devassistant.assistants.commands import run_command
from devassistant.logger import logger
from devassistant import yaml_snippet_loader

class YamlAssistant(assistant_base.AssistantBase):
    _dependencies = {}

    _run = []

    def proper_kwargs(self, **kwargs):
        """Returns kwargs possibly updated with values from .devassistant
        file, when appropriate."""
        if self.role == 'modifier':
            kwargs.update(run_command('dda_r', kwargs.get('path', '.'), **kwargs))
        return kwargs

    def logging(self, **kwargs):
        kwargs = self.proper_kwargs(**kwargs)
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
                formatter = logging.Formatter('%(asctime)-15s %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                handler.setLevel(getattr(logging, level.upper()))
                # register handler with the global logger
                logger.addHandler(handler)
            else:
                logger.warning('Unknown logger type {0}, ignoring.'.format(handler_type))

    def dependencies(self, **kwargs):
        kwargs = self.proper_kwargs(**kwargs)
        sections = [getattr(self, '_dependencies', [])]
        if self.role == 'modifier':
            # if subassistant_path is "foo bar baz", then search for dependency sections
            # _dependencies_foo, _dependencies_foo_bar, _dependencies_foo_bar_baz
            for i in range(1, len(kwargs['subassistant_path']) + 1):
                possible_dep_section = '_dependencies_{0}'.format('_'.join(kwargs['subassistant_path'][:i]))
                if possible_dep_section in dir(self):
                    sections.append(getattr(self, possible_dep_section))
        # install these dependencies in any case
        for arg in kwargs:
            if '_dependencies_{0}'.format(arg) in dir(self):
                sections.append(getattr(self, '_dependencies_{0}'.format(arg)))

        for sect in sections:
            self._dependencies_section(sect)

    def _dependencies_section(self, section, **kwargs):
        for dep in section:
            dep_type, dep_list = dep.popitem()
            # rpm dependencies (can't handle anything else yet)
            if dep_type == 'rpm':
                self._install_dependencies(*dep_list, **kwargs)
            elif dep_type == 'snippet':
                snippet, section_name = self._get_snippet_and_section_name(dep_list, **kwargs)
                section = snippet.get_dependencies_section(section_name) if snippet else None
                if section:
                    self._dependencies_section(section, **kwargs)
                else:
                    logger.warning('Couldn\'t find dependencies section "{0}", in snippet {1}, skipping.'.format(section_name,
                                                                                                                 dep_list.split('(')[0]))
            else:
                logger.warning('Unknown dependency type {0}, skipping.'.format(dep_type))

    def run(self, **kwargs):
        kwargs = self.proper_kwargs(**kwargs)
        if self.role == 'modifier':
            to_run = self._get_section_to_run(section='run_{0}'.format('_'.join(kwargs['subassistant_path'])),
                                              kwargs_override=True,
                                              **kwargs)
        else:
            to_run = self._get_section_to_run(section='run', kwargs_override=True, **kwargs)
        if 'pre_run' in dir(self):
            self._run_one_section(self.pre_run, kwargs)
        self._run_one_section(to_run, kwargs)
        if 'post_run' in dir(self):
            self._run_one_section(self.post_run, kwargs)

    def _run_one_section(self, section, kwargs):
        execute_else = False

        for i, command_dict in enumerate(section):
            for comm_type, comm in command_dict.items():
                if comm_type.startswith('run'):
                    s = self._get_section_to_run(section=comm, kwargs_override=False, **kwargs)
                    # use copy of kwargs, so that local kwargs don't get modified
                    self._run_one_section(s, copy.deepcopy(kwargs))
                elif comm_type == 'snippet':
                    snippet, section_name = self._get_snippet_and_section_name(comm, **kwargs)
                    # don't shadow "section" variable because we need to access it in sys.excepthook
                    sect = snippet.get_run_section(section_name) if snippet else None
                    if sect:
                        # push and pop snippet's files into kwargs
                        if '__files__' in kwargs:
                            kwargs['__files__'].append(snippet.get_files_section())
                        else:
                            kwargs['__files__'] = [snippet.get_files_section()]
                        # use copy of kwargs, so that local kwargs don't get modified
                        self._run_one_section(sect, copy.deepcopy(kwargs))
                        kwargs['__files__'].pop()
                    else:
                        logger.warning('Couldn\'t find run section "{0}", in snippet {1} skipping.'.format(section_name,
                                                                                                           comm.split('(')[0]))
                elif comm_type.startswith('$'):
                    # intentionally pass kwargs as dict, not as keywords
                    self._assign_variable(comm_type, comm, kwargs)
                elif comm_type.startswith('if'):
                    # check returned False (exit code != 0), because if commands succeeds without output, we get empty string
                    if self._evaluate(comm_type[2:].strip(), **kwargs) != False:
                        # run with original kwargs, so that they might be changed for code after this if
                        self._run_one_section(comm, kwargs)
                    elif len(section) > i + 1:
                        next_section_dict = section[i + 1]
                        next_section_comm_type, next_section_comm = list(next_section_dict.items())[0]
                        if next_section_comm_type == 'else':
                            execute_else = True
                elif comm_type == 'else':
                    # else on its own means error, otherwise execute it
                    if not list(section[i - 1].items())[0][0].startswith('if'):
                        logger.warning('Yaml error: encountered "else" with no associated "if", skipping.')
                    elif execute_else:
                        execute_else = False
                        # run with original kwargs, so that they might be changed for code after this if
                        self._run_one_section(comm, kwargs)
                else:
                    files = kwargs['__files__'][-1] if kwargs.get('__files__', None) else self._files
                    run_command(comm_type, CommandFormatter.format(comm, self.template_dir, files, **kwargs), **kwargs)

    def _get_section_to_run(self, section, kwargs_override=False, **kwargs):
        """Returns the proper section to run.
        Args:
            section: name of section to run
            kwargs_override: whether or not first of [_run_{arg} for arg in kwargs] is preffered over specified section
            **kwargs: devassistant arguments
        Returns:
            section to run - dict (if not found, returns empty dict)
        """
        to_run = {}

        if section:
            underscored = '_' + section
            if underscored in dir(self):
                to_run = getattr(self, underscored)

        if kwargs_override:
            for method in dir(self):
                if method.startswith('_run_'):
                    if method[len('_run_'):] in kwargs:
                        to_run = getattr(self, method)

        if not to_run:
            logger.debug('Couldn\'t find section {0} or any other appropriate.'.format(section))
        return to_run

    def _get_snippet_and_section_name(self, snippet_call, **kwargs):
        # if there is parenthesis, then snippet is being called with argument
        snippet_tuple = snippet_call.split('(')
        snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(snippet_tuple[0])
        section_name = snippet_tuple[1].strip(')') if len(snippet_tuple) > 1 else ''
        return (snippet, section_name)

    def _assign_variable(self, variable, comm, kwargs):
        """Assigns value of another variable or result of command to given variable.
        The result is then put into kwargs (overwriting original value, if already there).
        Note, that unlike other methods, this method has to accept kwargs, not **kwargs.

        If comm evaluates to something that is false, empty string is assigned to variable.

        Args:
            variable: variable to assign to
            comm: either another variable or command to run
        """
        var_name = self._get_var_name(variable)
        kwargs[var_name] = self._evaluate(comm, **kwargs) or ''

    def _get_var_name(self, dolar_variable):
        name = dolar_variable.strip()[1:]
        return name.strip('{}')

    def _evaluate(self, expression, **kwargs):
        result = True
        invert_result = False
        expr = expression.strip()
        if expr.startswith('not '):
            invert_result = True
            expr = expr[4:]

        if expr.startswith('$'):
            var_name = self._get_var_name(expr)
            result = kwargs.get(var_name, False)
        elif expr.startswith('defined '):
            result = self._get_var_name(expr[8:]) in kwargs
        else:
            try:
                result = run_command('cl_n', CommandFormatter.format(expr, self.template_dir, self._files, **kwargs), **kwargs)
            except exceptions.RunException:
                result = False

        return result if not invert_result else not result
