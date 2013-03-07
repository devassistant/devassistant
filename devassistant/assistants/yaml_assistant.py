import logging
import os
import string

import plumbum

from devassistant import assistant_base
from devassistant import exceptions
from devassistant import settings
from devassistant.command_helpers import ClHelper, RPMHelper, YUMHelper, PathHelper
from devassistant.logger import logger

class YamlAssistant(assistant_base.AssistantBase):
    _dependencies = {}

    _fail_if = []
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

    def errors(self, **kwargs):
        errors = []

        for command_dict in self._fail_if:
            for comm_type, comm in command_dict.items():
                if comm_type.startswith('cl'):
                    try:
                        a = self._format(comm, **kwargs)
                        self._format_and_run_cl_command(comm_type, comm, **kwargs)
                        # command succeeded -> error
                        errors.append('Cannot proceed because command returned 0: {0}'.format(a))
                    except exceptions.RunException:
                        pass # everything ok, go on
                elif comm_type.startswith('log'):
                    self._log(comm_type, comm, **kwargs)
                else:
                    logger.warning('Unknown action type {0}, skipping.'.format(comm_type))

        return errors

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
                if comm_type.startswith('cl'):
                    self._format_and_run_cl_command(comm_type, comm, **kwargs)
                elif comm_type.startswith('log'):
                    self._log(comm_type, comm, **kwargs)
                elif comm_type.startswith('dda'):
                    self._dot_devassistant_comm(comm_type, comm, **kwargs)
                elif comm_type == 'github':
                    self._github_comm(comm_type, comm, **kwargs)
                elif comm_type.startswith('run'):
                    s = self._get_section_to_run(section=comm, kwargs_override=False, **kwargs)
                    self._run_one_section(s, **kwargs)
                elif comm_type.startswith('$'):
                    # intentionally pass kwargs as dict, not as keywords
                    self._assign_variable(comm_type, comm, kwargs)
                elif comm_type.startswith('if'):
                    if self._evaluate_condition(comm_type[2:].strip(), **kwargs):
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
                    logger.warning('Unknown action type {0}, skipping.'.format(comm_type))

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
            logger.warning('Couldn\'t find section {0} or any other appropriate.'.format(section))
        return to_run


    def _dot_devassistant_comm(self, comm_type, comm, **kwargs):
        if comm_type == 'dda_c':
            self._dot_devassistant_create(self._format(comm, **kwargs), **kwargs)
        else:
            logger.warning('Unknown .devassistant command {0}, skipping.'.format(comm_type))

    def _assign_variable(self, variable, comm, kwargs):
        """Assigns value of another variable or result of command to given variable.
        The result is then put into kwargs (overwriting original value, if already there).
        Note, that unlike other methods, this method has to accept kwargs, not **kwargs.

        Args:
            variable: variable to assign to
            comm: either another variable or command to run
        """
        var_name = self._get_var_name(variable)
        # if comm is another variable, just assign its value, else it's cli command => run it
        if comm[0] == '$':
            kwargs[var_name] = kwargs.get(self._get_var_name(comm), '')
        else:
            try:
                kwargs[var_name] = self._format_and_run_cl_command('cl', comm, **kwargs) or ''
            except exceptions.RunException:
                kwargs[var_name] = ''

    def _get_var_name(self, dolar_variable):
        name = dolar_variable[1:]
        return name.strip('{}')

    def _github_comm(self, comm_type, comm, **kwargs):
        if comm_type == 'github':
            if comm == 'register':
                self._github_register(**kwargs)
            elif comm == 'remote':
                self._github_remote(**kwargs)
            else:
                logger.warning('Unknow github command {0}, skipping.'.format(comm))
        else:
            logger.warning('Unknown github command {0}, skipping.'.format(comm_type))

    def _evaluate_condition(self, condition, **kwargs):
        result = True
        invert_result = False
        cond = condition.strip()
        if cond.startswith('not '):
            invert_result = True
            cond = cond[4:]

        if cond.startswith('$'):
            var_name = self._get_var_name(cond)
            if var_name in kwargs and kwargs[var_name]:
                result = True
            else:
                result = False
        else:
            try:
                c = self._format_and_run_cl_command('cl', cond, **kwargs)
                result = True
            except exceptions.RunException:
                result = False
        return result != invert_result # != is basically xor

    def _format_and_run_cl_command(self, command_type, command, **kwargs):
        c = self._format(command, **kwargs)
        fg = False
        i = False
        if 'f' in command_type:
            fg = True
        if 'i' in command_type:
            i = True
        try:
            result = ClHelper.run_command(c, fg, i)
        except plumbum.ProcessExecutionError as e:
            raise exceptions.RunException(e)

        return result.strip() if hasattr(result, 'strip') else result

    def _log(self, comm_type, log_msg, **kwargs):
        if comm_type in map(lambda x: 'log_{0}'.format(x), settings.LOG_LEVELS_MAP):
            logger.log(logging._levelNames[settings.LOG_LEVELS_MAP[comm_type[-1]]], self._format(log_msg, **kwargs))
        else:
            logger.warning('Unknown logging command {0} with message {1}'.format(comm_type, log_msg))

    def _format(self, comm, **kwargs):
        # If command is false/true in yaml file, it gets coverted to False/True
        # which is bool object => convert
        if isinstance(comm, bool):
            comm = str(comm).lower()

        new_comm = []
        if not isinstance(comm, list):
            parts_list = comm.split()
        else:
            parts_list = comm

        # replace parts that match something from _files (can be either name
        # if "&" didn't expand in yaml; or the dict if "&" did expand)
        for c in parts_list:
            if isinstance(c, dict):
                # TODO: raise a proper error if c['source'] is not present
                new_comm.append(os.path.join(self.template_dir, c['source']))
            elif c.startswith('*'):
                c_file = c[1:].strip('{}')
                if c_file in self._files:
                    new_comm.append(os.path.join(self.template_dir, self._files[c_file]['source']))
                else:
                    new_comm.append(c)
            else:
                new_comm.append(c)

        new_comm = ' '.join(new_comm)

        # substitute cli arguments for their values
        return string.Template(new_comm).safe_substitute(kwargs)
