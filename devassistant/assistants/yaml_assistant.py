import copy
import functools
import logging
import os

from devassistant import argument
from devassistant import assistant_base
from devassistant import exceptions
from devassistant.assistants.command_formatter import CommandFormatter
from devassistant.assistants.commands import run_command
from devassistant.logger import logger
from devassistant import yaml_loader
from devassistant import yaml_snippet_loader
from devassistant import package_managers

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

class YamlAssistant(assistant_base.AssistantBase):
    def __init__(self, name, parsed_yaml, path, template_dir, fully_loaded=True, role='creator'):
        self.name = name
        self.parsed_yaml = parsed_yaml
        self.path = path
        self.template_dir = template_dir
        self.fully_loaded = fully_loaded
        self.role = role
        self.stop_flag = False

    @property
    def parsed_yaml(self):
        return self._parsed_yaml

    @parsed_yaml.setter
    def parsed_yaml(self, value):
        self._parsed_yaml = value

        self.template_dir = value.get('template_dir', self.template_dir)
        self.fullname = value.get('fullname', '')
        self.description = value.get('description', '')
        self.args = self._construct_args(value.get('args', {}))

        self._files = value.get('files', {})
        self._logging = value.get('logging', [])
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

    @needs_fully_loaded
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

    @needs_fully_loaded
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
        skip_else = False
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
                elif dep_type in package_managers.managers.keys(): # handle known types of deps the same, just by appending to "deps" list
                    deps.append({dep_type: dep_list})
                elif dep_type.startswith('if'):
                    possible_else = None
                    if len(section) > i + 1: # do we have "else" clause?
                        possible_else = list(section[i + 1].items())[0]
                    _, skip_else, to_run = self._get_section_from_condition((dep_type, dep_list), possible_else, **kwargs)
                    if to_run:
                        deps.extend(self._dependencies_section(to_run, **kwargs))
                elif dep_type == 'else':
                    # else on its own means error, otherwise execute it
                    if not skip_else:
                        logger.warning('Yaml error: encountered "else" with no associated "if", skipping.')
                    skip_else = False
                else:
                    logger.warning('Unknown dependency type {0}, skipping.'.format(dep_type))

        return deps

    @needs_fully_loaded
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

        kwargs['__assistant__'] = self
        if self._pre_run:
            self._run_one_section(self._pre_run, kwargs)
        self._run_one_section(to_run, kwargs)
        if self._post_run:
            self._run_one_section(self._post_run, kwargs)

    def _run_one_section(self, section, kwargs):
        skip_else = False

        for i, command_dict in enumerate(section):
            if self.stop_flag:
                break
            for comm_type, comm in command_dict.items():
                if comm_type.startswith('call'):
                    # calling workflow:
                    # 1) get proper run section (either from self or from snippet)
                    # 2) if running snippet, add its files to kwargs['__files__']
                    # 3) actually run
                    # 4) if running snippet, pop its files from kwargs['__files__']
                    sect = self._get_section_from_call(comm, 'run')

                    if sect is None:
                        logger.warning('Couldn\'t find section to run: {0}.'.format(comm))
                        continue

                    if self._is_snippet_call(comm, **kwargs):
                        # we're calling a snippet => add files and template_dir to kwargs
                        snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(comm.split('.')[0])

                        if '__files__' not in kwargs:
                            kwargs['__files__'] = []
                            kwargs['__template_dir__'] = []
                        kwargs['__files__'].append(snippet.get_files_section())
                        kwargs['__template_dir__'].append(snippet.get_template_dir())

                    self._run_one_section(sect, copy.deepcopy(kwargs))

                    if self._is_snippet_call(comm, **kwargs):
                        kwargs['__files__'].pop()
                        kwargs['__template_dir__'].pop()
                elif comm_type.startswith('$'):
                    # intentionally pass kwargs as dict, not as keywords
                    try:
                        self._assign_variable(comm_type, comm, kwargs)
                    except exceptions.YamlSyntaxError as e:
                        logger.error(e)
                        raise e
                elif comm_type.startswith('if'):
                    possible_else = None
                    if len(section) > i + 1: # do we have "else" clause?
                        possible_else = list(section[i + 1].items())[0]
                    _, skip_else, to_run = self._get_section_from_condition((comm_type, comm), possible_else, **kwargs)
                    if to_run:
                        # run with original kwargs, so that they might be changed for code after this if
                        self._run_one_section(to_run, kwargs)
                elif comm_type == 'else':
                    if not skip_else:
                        logger.warning('Yaml error: encountered "else" with no associated "if", skipping.')
                    skip_else = False
                elif comm_type.startswith('for'):
                    # syntax: "for $i in $x: <section> or "for $i in cl_command: <section>"
                    try:
                        control_var, expression = self._parse_for(comm_type)
                    except exceptions.YamlSyntaxError as e:
                        logger.error(e)
                        raise e
                    try:
                        eval_expression = self._evaluate()
                    except exceptions.YamlSyntaxError as e:
                        logger.log(e)
                        raise e

                    for i in eval_expression:
                        kwargs[control_var] = i
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
                    template_dir = kwargs['__template_dir__'][-1] if kwargs.get('__template_dir__', None) else self.template_dir
                    run_command(comm_type, CommandFormatter.format(comm_type, comm, template_dir, files, **kwargs), **kwargs)

    def _is_snippet_call(self, cmd_call, **kwargs):
        return not (cmd_call == 'self' or cmd_call.startswith('self.'))

    def _parse_for(self, control_line, **kwargs):
        """Returns name of loop control variable and expression to iterate.
        Expression can be either a variable (will be returned as it is, e.g.
        "${foo}") or a commandline call.

        For example:
        - given "for $i in $foo", returns ('i', '$foo')
        - given "for ${i} in ls $foo", returns ('i', 'ls $foo')
        """
        for_parts = control_line.split(None, 3)
        error = 'For loop call must be in form \'for $var in expression\', got: ' + control_line
        if for_parts[0] != 'for':
            pass # specify the error more?
        elif for_parts[2] != 'in':
            pass # specify the error more?
        elif len(for_parts) != 4:
            pass # specify the error more?
        else:
            try:
                control_var = self._get_var_name(for_parts[1])
                error = None
            except exceptions.YamlSyntaxError:
                pass # specify the error more?

        if error:
            raise exceptions.YamlSyntaxError(error)

        return (control_var, for_parts[3])

    def _get_section_from_condition(self, if_section, else_section=None, **kwargs):
        """Returns section that should be used from given if/else sections by evaluating given condition.

        Args:
            if_section - section with if clause
            else_section - section that *may* be else clause (just next section after if_section,
                           this method will check if it really is else); possibly None if not present

        Returns:
            tuple (<0 or 1>, <True or False>, section), where
            - the first member says whether we're going to "if" section (0) or else section (1)
            - the second member says whether we should skip next section during further evaluation
              (True or False - either we have else to skip, or we don't)
            - the third member is the appropriate section to run or None if there is only "if"
              clause and condition evaluates to False
        """
        # check if else section is really else
        skip = True if else_section is not None and else_section[0] == 'else' else False
        if self._evaluate(if_section[0][2:].strip(), **kwargs)[0]:
            return (0, skip, if_section[1])
        else:
            return (1, skip, else_section[1]) if skip else (1, skip, None)

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
            section to run - dict, None if not found
        """

        section = None
        call_parts = cmd_call.split('.')
        section_name = call_parts[1] if len(call_parts) > 1 else section_type

        if call_parts[0] == 'self':
            section = getattr(self, '_' + section_name, None)
        else: # snippet
            try:
                snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(call_parts[0])
                if section_type == 'run':
                    section = snippet.get_run_section(section_name) if snippet else None
                else:
                    section = snippet.get_dependencies_section(section_name) if snippet else None
            except exceptions.SnippetNotFoundException:
                section = None

        return section

    def _get_section_to_run(self, section, kwargs_override=False, **kwargs):
        """Returns the proper section to run.
        Args:
            section: name of section to run
            kwargs_override: whether or not first of [_run_{arg} for arg in kwargs] is preffered over specified section
            **kwargs: devassistant arguments
        Returns:
            section to run - dict, None if not found
        """
        to_run = None

        if section:
            underscored = '_' + section
            if underscored in dir(self):
                to_run = getattr(self, underscored)

        if kwargs_override:
            for method in dir(self):
                if method.startswith('_run_'):
                    if method[len('_run_'):] in kwargs:
                        to_run = getattr(self, method)

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
        name = name.strip('"\'')
        if not name.startswith('$'):
            raise exceptions.YamlSyntaxError('Not a proper variable name: ' + dolar_variable)
        name = name[1:] # strip the dollar
        return name.strip('{}')

    def _evaluate(self, expression, **kwargs):
        """Evaluates given expression - can be one of
        - $foo
        - "$foo"
        - $(cl command)

        Returns:
            tuple (success, value), where
            - success means whether variable was found or cl command returned zero
            - value is the evaluated value :)

        Raises:
            exceptions.YamlSyntaxError if expression is malformed
        """
        # was command successful?
        success = True
        # command output
        output = ''
        invert_success = False
        expr = expression.strip()
        if expr.startswith('not '):
            invert_success = True
            expr = expr[4:]

        if expr.startswith('$('): # only one expression: "$(expression)"
            try:
                output = run_command('cl_n', CommandFormatter.format('cl', expr[2:-1], self.template_dir, self._files, **kwargs), **kwargs)
            except exceptions.RunException as ex:
                success = False
                output = ex.output
        elif expr.startswith('$') or expr.startswith('"$'):
            var_name = self._get_var_name(expr)
            if var_name in kwargs and kwargs[var_name]:
                success = True
                output = kwargs[var_name]
            else:
                success = False
        elif expr.startswith('defined '):
            success = self._get_var_name(expr[8:]) in kwargs
        else:
            raise exceptions.YamlSyntaxError('Not a valid expression: ' + expression)

        return (success if not invert_success else not success, output)

    @needs_fully_loaded
    def stop(self):
        """ This function is used for stopping devassistant from GUI
        """
        self.stop_flag = True
