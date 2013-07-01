import os
import re
import string

class CommandFormatter(object):
    @classmethod
    def format(cls, comm_type, comm, template_dir, files, **kwargs):
        if comm_type.startswith('dependencies'): # don't process dependencies
            return comm

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
                new_comm.append(os.path.join(template_dir, c['source']))
            elif c.startswith('*'):
                c_file = c[1:].strip('{}')
                if c_file in files:
                    new_comm.append(os.path.join(template_dir, files[c_file]['source']))
                else:
                    new_comm.append(c)
            else:
                new_comm.append(c)

        new_comm = ' '.join(new_comm)

        # substitute cli arguments for their values
        substituted = string.Template(new_comm).safe_substitute(kwargs)

        # we want to do homedir expansion in quotes (which bash doesn't)
        # therefore we must hack around this here
        regex = re.compile('\\\\*~')
        return regex.sub(cls._homedir_expand, substituted)

    @classmethod
    def _homedir_expand(cls, matchobj):
        if len(matchobj.group(0)) % 2 == 0:
            # even length => odd number of backslashes => eat one and don't expand
            return matchobj.group(0)[:-2] + '~'
        else:
            # odd length => even number of backslashes => expand an
            return matchobj.group(0)[:-1] + os.path.expanduser('~')
