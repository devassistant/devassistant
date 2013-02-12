import logging
import os
import string

import plumbum

from devassistant import assistant_base
from devassistant import exceptions
from devassistant import settings
from devassistant.command_helpers import ClHelper, RPMHelper, YUMHelper
from devassistant.logger import logger

class YamlAssistant(assistant_base.AssistantBase):
    _dependencies = {}

    _fail_if = []
    _run = []

    def errors(self, **kwargs):
        errors = []

        for one_action in self._fail_if:
            for action_type, action in one_action.items():
                if action_type == 'cl':
                    try:
                        a = self.format_command(action, **kwargs)
                        result = ClHelper.run_command(a)
                        # command succeeded -> error
                        errors.append('Cannot proceed because command returned 0: {0}'.format(a))
                    except plumbum.ProcessExecutionError:
                        pass # everything ok, go on
                elif action_type == 'log':
                    self.log(action)
                else:
                    logger.warning('Unkown action type {0}, skipping.'.format(action_type))

        return errors

    def dependencies(self, **kwargs):
        to_install = []
        # rpm dependencies (can't handle anything else yet)
        for dep_type, dep_list in self._dependencies.items():
            if dep_type == 'rpm':
                for dep in dep_list:
                    if dep.startswith('@'):
                        if not YUMHelper.is_group_installed(dep):
                            to_install.append(dep)
                    else:
                        if not RPMHelper.is_rpm_installed(dep):
                            to_install.append(dep)
            else:
                logger.warning('Unkown dependency type {0}, skipping.'.format(dep_type))

        if to_install:
            YUMHelper.install(*to_install)

    def run(self, **kwargs):
        # determine which run* section to invoke
        to_run = self._run
        for method in dir(self):
            if method.startswith('_run_'):
                parameter = method.split('_', 2)[-1]
                if kwargs.get(parameter, False):
                    to_run = getattr(self, method)

        for command_dict in to_run:
            for comm_type, comm in command_dict.items():
                if comm_type == 'cl':
                    c = self.format_command(comm, **kwargs)
                    try:
                        result = ClHelper.run_command(c)
                    except plumbum.ProcessExecutionError as e:
                        raise exceptions.RunException(e)
                elif comm_type == 'log':
                    self.log(comm)
                else:
                    logger.warning('Unkown action type {0}, skipping.'.format(comm_type))

    def log(self, log_action):
        # make level lowercase
        log_action = (log_action[0].upper(), log_action[1])
        if log_action[0] in logging._levelNames:
            logger.log(logging._levelNames[log_action[0]], log_action[1])
        else:
            logger.warning('Unknow logging level {0}, with message {1}'.format(*log_action))

    def format_command(self, comm, **kwargs):
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
            elif c.startswith('&'):
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
