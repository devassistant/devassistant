import os
import re
import string

from devassistant import exceptions
from devassistant.logger import logger
from devassistant import utils

class Command(object):
    _command_runners = None

    def __init__(self, comm_type, comm, kwargs):
        self.comm_type = comm_type
        self.comm = comm
        self.files_dir = kwargs.get('__files_dir__', [''])[-1]
        self.files = kwargs.get('__files__', [''])[-1]
        self.kwargs = kwargs

    def run(self):
        if not type(self)._command_runners:
            # avoid circular dependency between this module and command_runners
            type(self)._command_runners = utils.import_module('devassistant.command_runners')
        for cr in type(self)._command_runners.command_runners:
            if cr.matches(self): 
                return cr.run(self) 

        logger.warning('Unknown command type {0}, skipping.'.format(self.comm_type))

    def format_str(self):
        """Formats the given command as a string."""
        # If command is false/true in yaml file, it gets coverted to False/True
        # which is bool object => convert
        if isinstance(self.comm, bool):
            comm = str(self.comm).lower()
        else:
            comm = self.comm

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
                new_comm.append(os.path.join(self.files_dir, c['source']))
            elif c.startswith('*'):
                c_file = c[1:].strip('{}')
                if c_file in self.files:
                    new_comm.append(os.path.join(self.files_dir, self.files[c_file]['source']))
                else:
                    new_comm.append(c)
            else:
                new_comm.append(c)

        new_comm = ' '.join(new_comm)

        # substitute cli arguments for their values
        substituted = string.Template(new_comm).safe_substitute(self.kwargs)

        # we want to do homedir expansion in quotes (which bash doesn't)
        # therefore we must hack around this here
        regex = re.compile('\\\\*~')
        return regex.sub(type(self)._homedir_expand, substituted)

    def format_list(self):
        """Formats the given command as a list."""
        if isinstance(self.comm, list):
            return self.comm
        elif isinstance(self.comm, str) and self.comm.startswith('$'):
            return self.kwargs.get(self.comm.strip()[1:], [])
        else:
            raise exceptions.YamlTypeError('{ct} expected list, not {t}'.format(ct=self.comm_type, t=type(self.comm)))

    @classmethod
    def _homedir_expand(cls, matchobj):
        if len(matchobj.group(0)) % 2 == 0:
            # even length => odd number of backslashes => eat one and don't expand
            return matchobj.group(0)[:-2] + '~'
        else:
            # odd length => even number of backslashes => expand an
            return matchobj.group(0)[:-1] + os.path.expanduser('~')
