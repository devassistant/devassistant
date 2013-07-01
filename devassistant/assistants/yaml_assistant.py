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
            # don't rewrite old values
            # first get the new ones and then update them with the old
            new_kwargs = run_command('dda_r', kwargs.get('path', '.'), **kwargs)
            new_kwargs.update(kwargs)
            kwargs = new_kwargs
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
                formatter = logging.Formatter('%(asctime)-15s [%(event_type)] %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                handler.setLevel(getattr(logging, level.upper()))
                # register handler with the global logger
                logger.addHandler(handler)
            else:
                logger.warning('Unknown logger type {0}, ignoring.'.format(handler_type))

    def dependencies(self, **kwargs):
        """Returns all dependencies of this assistant with regards to specified kwargs.

        This is list of mappings of dependency types to actual dependencies
        (keeps order, types can repeat), e.g.
        Example:
        [{'rpm', ['rubygems']}, {'gem', ['mygem']}, {'rpm', ['spam']}, ...]
        """

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

        deps = []

        for sect in sections:
            deps.extend(self._dependencies_section(sect, **kwargs))

        return deps

    def _dependencies_section(self, section, **kwargs):
        # "deps" is the same structure as gets returned by "dependencies" method
        execute_else = False
        deps = []

        for i, dep in enumerate(section):
            for dep_type, dep_list in dep.items():
                # rpm dependencies (can't handle anything else yet)
                if dep_type == 'call':
                    section = self._get_section_from_call(dep_list, 'dependencies', **kwargs)
                    if section is not None:
                        deps.extend(self._dependencies_section(section, **kwargs))
                    else:
                        logger.warning('Couldn\'t find dependencies section "{0}", in snippet {1}, skipping.'.format(dep_list.split('.')))
                elif dep_type in ['rpm']: # handle known types of deps the same, just by appending to "deps" list
                    deps.append({dep_type: dep_list})
                ### TODO: this is not completely DRY, the conditionals here use completely the same logic as in run sections
                elif dep_type.startswith('if'):
                    if self._evaluate(dep_type[2:].strip(), **kwargs)[0]:
                        deps.extend(self._dependencies_section(dep_list, **kwargs))
                    elif len(section) > i + 1:
                        next_section_dict = section[i + 1]
                        next_section_dep_type, next_section_dep = list(next_section_dict.items())[0]
                        if next_section_dep_type == 'else':
                            execute_else = True
                elif dep_type == 'else':
                    # else on its own means error, otherwise execute it
                    if not list(section[i - 1].items())[0][0].startswith('if'):
                        logger.warning('Yaml error: encountered "else" with no associated "if", skipping.')
                    elif execute_else:
                        execute_else = False
                        deps.extend(self._dependencies_section(dep_list, **kwargs))
                else:
                    logger.warning('Unknown dependency type {0}, skipping.'.format(dep_type))

        return deps

    def run(self, **kwargs):
        kwargs = self.proper_kwargs(**kwargs)
        if self.role == 'modifier':
            # try to get a section to run from the most specialized one to the least specialized one
            # e.g. first run_python_django, then run_python and then just run
            for i in range(len(kwargs['subassistant_path']), -1, -1):
                path = '_'.join(kwargs['subassistant_path'][0:i])
                if path:
                    path = '_' + path
                to_run = self._get_section_to_run(section='run{path}'.format(path=path),
                                                  kwargs_override=True,
                                                  **kwargs)
                if to_run:
                    break
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
                if comm_type.startswith('call'):
                    # calling workflow:
                    # 1) get proper run section (either from self or from snippet)
                    # 2) if running snippet, add its files to kwargs['__files__']
                    # 3) actually run
                    # 4) if running snippet, pop its files from kwargs['__files__']
                    sect = self._get_section_from_call(comm, 'run')
                    if self._is_snippet_call(comm, **kwargs):
                        # we're calling a snippet => add files to kwargs
                        snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(comm.split('.')[0])
                        if '__files__' not in kwargs:
                            kwargs['__files__'] = []
                        kwargs['__files__'].append(snippet.get_files_section())

                    if sect is None:
                        logger.warning('No section to run: {0}.'.format(comm))
                    else:
                        self._run_one_section(sect, copy.deepcopy(kwargs))

                    if self._is_snippet_call(comm, **kwargs):
                        kwargs['__files__'].pop()
                elif comm_type.startswith('$'):
                    # intentionally pass kwargs as dict, not as keywords
                    self._assign_variable(comm_type, comm, kwargs)
                elif comm_type.startswith('if'):
                    if self._evaluate(comm_type[2:].strip(), **kwargs)[0]:
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
                elif comm_type.startswith('scl'):
                    if '__scls__' not in kwargs:
                        kwargs['__scls__'] = []
                    # list of lists of scl names
                    kwargs['__scls__'].append(comm_type.split()[1:])
                    self._run_one_section(comm, kwargs)
                    kwargs['__scls__'].pop()
                else:
                    files = kwargs['__files__'][-1] if kwargs.get('__files__', None) else self._files
                    run_command(comm_type, CommandFormatter.format(comm_type, comm, self.template_dir, files, **kwargs), **kwargs)

    def _is_snippet_call(self, cmd_call, **kwargs):
        return not (cmd_call == 'self' or cmd_call.startswith('self.'))

    def _get_section_from_call(self, cmd_call, section_type, **kwargs):
        """Returns a section form call.

        Examples:
            if section_type == dependencies, then
              cmd_call == self.dependencies_bar returns content of dependencies_bar from this assistant
            if section_type == run, then
              cmd_call == self.run_foo returns run_foo of this assistant
              cmd_call == eclipse.run_python returns run_python section of eclipse snippet

        Args:
            cmd_call - a string with the call, e.g. "eclipse.run_python"
            section_type - either "dependencies" or "run"

        Returns:
            Section (a dict), if found, otherwise None."""

        section = None
        call_parts = cmd_call.split('.')
        section_name = call_parts[1] if len(call_parts) > 1 else section_type

        if call_parts[0] == 'self':
            section = getattr(self, '_' + section_name, None)
        else:
            snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(call_parts[0])
            if section_type == 'run':
                section = snippet.get_run_section(section_name) if snippet else None
            else:
                section = snippet.get_dependencies_section(section_name) if snippet else None

        return section

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

    def _assign_variable(self, variable, comm, kwargs):
        """Assigns value of another variable or result of command to given variable.
        The result is then put into kwargs (overwriting original value, if already there).
        Note, that unlike other methods, this method has to accept kwargs, not **kwargs.

        Cl commands store both stdout and stderr (as a single string) as the variable value.

        Even if comm evaluates to something that is false, output is still stored and
        this method doesn't fail.

        Args:
            variable: variable to assign to
            comm: either another variable or command to run
        """
        var_name = self._get_var_name(variable)
        kwargs[var_name] = self._evaluate(comm, **kwargs)[1]

    def _get_var_name(self, dolar_variable):
        name = dolar_variable.strip()
        name = name.strip('"')[1:]
        return name.strip('{}')

    def _evaluate(self, expression, **kwargs):
        # was command successful?
        success = True
        # command output
        output = ''
        invert_success = False
        expr = expression.strip()
        if expr.startswith('not '):
            invert_success = True
            expr = expr[4:]

        if expr.startswith('$') or expr.startswith('"$'):
            var_name = self._get_var_name(expr)
            if var_name in kwargs and kwargs[var_name]:
                success = True
                output = kwargs[var_name]
            else:
                success = False
        elif expr.startswith('defined '):
            success = self._get_var_name(expr[8:]) in kwargs
        else:
            try:
                output = run_command('cl_n', CommandFormatter.format('cl', expr, self.template_dir, self._files, **kwargs), **kwargs)
            except exceptions.RunException as ex:
                success = False
                output = ex.output 

        return (success if not invert_success else not success, output)
