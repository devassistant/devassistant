import string

import plumbum

from devassistant import assistant_base
from devassistant import exceptions
from devassistant.command_helpers import RPMHelper, YUMHelper
from devassistant.logger import logger

class YamlAssistant(assistant_base.AssistantBase):
    _dependencies = {}

    _fail_if = []
    _run = []

    def errors(self, **kwargs):
        errors = []

        for one_action in self._fail_if:
            for action_type, action in one_action:
                if action_type == 'cl':
                    try:
                        a = self.format_command(action, **kwargs)
                        result = plumbum.local(a)
                        # command succeeded -> error
                        errors.append('Failed: {0}'.format(result))
                    except plumbum.ProcessExecutionError:
                        pass # everything ok, go on
                else:
                    logger.warning('Unkown action type {0}, skipping.'.format(action_type))

        return errors

    def dependencies(self, **kwargs):
        to_install = []
        # rpm dependencies (can't handle anything else yet)
        for dep_type, dep_list in self._dependencies:
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
        for command_dict in self._run:
            for comm_type, comm in command_dict.items():
                if comm_type == 'cl':
                    c = self.format_command(comm, **kwargs)
                    try:
                        result = plumbum.local(c)
                    except plumbum.ProcessExecutionError as e:
                        raise exceptions.RunException(e)
                else:
                    logger.warning('Unkown command type {0}, skipping.'.format(comm_type))

    def format_command(self, comm, **kwargs):
        new_comm = comm
        if isinstance(comm, list):
            # a list, usually including one or more dictionaries, where one or more
            # arguments include something from _files (value, not reference)
            parts_list = []
            for c in comm:
                if isinstance(c, dict):
                    # TODO: raise a proper error if c['source'] is not present
                    new_comm.append(c['source'])
                else:
                    parts_list.append(c)
            new_comm = ' '.join(parts_list)

        # substitute cli arguments for their values

        return string.Template(new_comm).safe_substitute(kwargs)
