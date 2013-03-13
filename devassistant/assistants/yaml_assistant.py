import logging
import os
import string

import plumbum

from devassistant import assistant_base
from devassistant import exceptions
from devassistant import settings
from devassistant.assistants.command_formatter import CommandFormatter
from devassistant.assistants.commands import run_command
from devassistant.command_helpers import ClHelper, RPMHelper, YUMHelper, PathHelper
from devassistant.logger import logger
from devassistant import yaml_snippet_loader

class YamlAssistant(assistant_base.AssistantBase):
    _dependencies = {}

    _run = []

    def logging(self, **kwargs):
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
        for sect in self._dependencies:
            condition, section = sect.popitem()
            if condition == 'default' or kwargs.get(condition[1:], False):
                self._dependencies_section(section)

    def _dependencies_section(self, section, **kwargs):
        for dep in section:
            dep_type, dep_list = dep.popitem()
            # rpm dependencies (can't handle anything else yet)
            if dep_type == 'rpm':
                self._install_dependencies(*dep_list, **kwargs)
            else:
                logger.warning('Unknown dependency type {0}, skipping.'.format(dep_type))

    def run(self, **kwargs):
        to_run = self._get_section_to_run(section='run', kwargs_override=True, **kwargs)
        self._run_one_section(to_run, **kwargs)

    def _run_one_section(self, section, **kwargs):
        execute_else = False

        for i, command_dict in enumerate(section):
            for comm_type, comm in command_dict.items():
                if comm_type.startswith('run'):
                    s = self._get_section_to_run(section=comm, kwargs_override=False, **kwargs)
                    self._run_one_section(s, **kwargs)
                elif comm_type.startswith('$'):
                    # intentionally pass kwargs as dict, not as keywords
                    self._assign_variable(comm_type, comm, kwargs)
                elif comm_type == 'snippet':
                    snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(comm)
                    if snippet:
                        self._run_one_section(snippet.run_section, **kwargs)
                    else:
                        logger.warning('Couldn\'t find snippet {0}, skipping.'.format(comm))
                elif comm_type.startswith('if'):
                    if self._evaluate(comm_type[2:].strip(), **kwargs):
                        self._run_one_section(comm, **kwargs)
                    elif len(section) > i + 1:
                        next_section_dict = section[i + 1]
                        next_section_comm_type, next_section_comm = next_section_dict.items()[0]
                        if next_section_comm_type == 'else':
                            execute_else = True
                elif comm_type == 'else':
                    # else on its own means error, otherwise execute it
                    if not section[i - 1].items()[0][0].startswith('if'):
                        logger.warning('Yaml error: encountered "else" with no associated "if", skipping.')
                    elif execute_else:
                        execute_else = False
                        self._run_one_section(comm, **kwargs)
                else:
                    run_command(comm_type, CommandFormatter.format(comm, self.template_dir, self._files, **kwargs), **kwargs)

    def _get_section_to_run(self, section, kwargs_override=False, **kwargs):
        to_run = None

        if section:
            underscored = '_' + section
            if underscored in dir(self):
                to_run = getattr(self, underscored)

        if kwargs_override:
            for method in dir(self):
                if method.startswith('_run_'):
                    if kwargs.get(method[len('_run_'):], False):
                        to_run = getattr(self, method)

        if not to_run:
            logger.debug('Couldn\'t find section {0} or any other appropriate.'.format(section))
        return to_run

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
                result = run_command('cl', CommandFormatter.format(expr, self.template_dir, self._files, **kwargs), **kwargs)
            except exceptions.RunException:
                result = False

        return result if not invert_result else not result
