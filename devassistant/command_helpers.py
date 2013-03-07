import os

import plumbum
from plumbum.cmd import ls, sudo

from devassistant import settings
from devassistant.logger import logger

class ClHelper(object):
    @classmethod
    def run_command(cls, cmd_str, fg=False, log_as_info=False):
        """Runs a command from string, e.g. "cp foo bar" """
        result = None
        split_string = cmd_str.split()

        for i, s in enumerate(split_string):
            if '~' in s:
                split_string[i] = os.path.expanduser(s)
        # hack for cd to behave like shell cd and stay in the directory
        if split_string[0] == 'cd':
            plumbum.local.cwd.chdir(split_string[1])
        else:
            cmd = plumbum.local[split_string[0]]
            fixed_args = cls._connect_quoted(split_string[1:])
            fixed_args = cls._strip_trailing_quotes(fixed_args)
            for i in fixed_args:
                cmd = cmd[i]
            # log the invocation
            log_string = settings.COMMAND_LOG_STRING.format(cmd=cmd)
            if log_as_info:
                logger.info(log_string)
            else:
                logger.debug(log_string)

            # actually invoke the command
            if fg:
                result = cmd & plumbum.FG
            else:
                result = cmd()

        return result

    @classmethod
    def _connect_quoted(cls, arg_list):
        """Returns list where quoted arguments to CL commands are not split
        into multiple items as in given arg_list. Certainly not an optimal
        solution (would need a finite state machine to do that properly...)

        See https://github.com/bkabrda/devassistant/issues/24 for problem report.
        Args:
            arg_list: list of arguments not containing the actual invoked binary
        Returns:
            list of arguments where no quoted strings are separated
        """
        i = 0
        proper_list = []
        constructing = []
        looking_for = None
        in_middle = False

        while i < len(arg_list):
            if in_middle:
                constructing.append(arg_list[i])
            elif not '"' in arg_list[i] and not "'" in arg_list[i] and not looking_for:
                proper_list.append(arg_list[i])
            else:
                if looking_for and looking_for in arg_list[i]:
                    constructing.append(arg_list[i])
                    proper_list.append(' '.join(constructing))
                    looking_for = None
                    in_middle = False
                    constructing = []
                elif looking_for and looking_for not in arg_list[i]:
                    constructing.append(arg_list[i])
                else:
                    single_i = arg_list[i].find("'")
                    double_i = arg_list[i].find('"')
                    looking_for = arg_list[i][single_i if single_i > -1 else double_i]
                    if arg_list[i].count(looking_for) % 2 == 0: # even number of quotes in this string => just add it
                        proper_list.append(arg_list[i])
                        looking_for = None
                    else:
                        constructing.append(arg_list[i])
            i += 1

        # append any remains from constructing (odd number of quotes/other problem...)
        proper_list.extend(constructing)

        return proper_list

    @classmethod
    def _strip_trailing_quotes(cls, arg_list):
        proper_list = []

        for arg in arg_list:
            proper_list.append(arg.strip('"\''))

        return proper_list

class RPMHelper(object):
    c_rpm = plumbum.local['rpm']

    @classmethod
    def rpm_q(cls, rpm_name):
        try:
            return cls.c_rpm('-q', rpm_name).strip()
        except plumbum.ProcessExecutionError:
            return False

    @classmethod
    def is_rpm_installed(cls, rpm_name):
        logger.info('Checking for presence of {0}...'.format(rpm_name))

        found_rpm = cls.rpm_q(rpm_name)
        if found_rpm:
            logger.info('Found %s', found_rpm)
        else:
            logger.info('Not found')
        return found_rpm

    @classmethod
    def was_rpm_installed(cls, rpm_name):
        # TODO: handle failure
        found_rpm = cls.rpm_q(rpm_name)
        logger.info('Installed %s', found_rpm)
        return found_rpm


class YUMHelper(object):
    c_yum = plumbum.local['yum']

    @classmethod
    def install(cls, *args):
        cmd = cls.c_yum[ 'install'] #TODO: do we really want to assume yes?
        logger.info('Installing: {0}'.format(', '.join(args)))
        for arg in args:
            cmd = cmd[arg]
        try:
            (sudo[cmd]) & plumbum.FG
            return args
        except plumbum.ProcessExecutionError:
            return False

    @classmethod
    def is_group_installed(cls, group):
        cmd = cls.c_yum['group', 'list', '"{0}"'.format(group)]
        logger.info('Checking for presence of group {0}...'.format(group))

        output = cmd()
        if 'Installed Groups' in output:
            logger.info('Found %s', group)
            return True

        logger.info('Not found')
        return False

class PathHelper(object):
    c_cp = plumbum.local['cp']
    c_mkdir = plumbum.local['mkdir']

    @classmethod
    def path_exists(cls, path):
        try:
            return ls(path).strip()
        except plumbum.ProcessExecutionError:
            return False

    @classmethod
    def mkdir_p(cls, path):
        try:
            return cls.c_mkdir('-p', path)
        except plumbum.ProcessExecutionError:
            return False

    @classmethod
    def cp(cls, src, dest):
        try:
            return cls.c_cp(src, dest)
        except plumbum.ProcessExecutionError:
            return False
