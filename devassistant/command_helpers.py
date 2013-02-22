import os

import plumbum
from plumbum.cmd import ls, sudo

from devassistant import settings
from devassistant.logger import logger

class ClHelper(object):
    @classmethod
    def run_command(cls, cmd_str, fg=False, log_as_info=False):
        """Runs a command from string, e.g. "cp foo bar" """
        split_string = cmd_str.split()
        for i, s in enumerate(split_string):
            if '~' in s:
                split_string[i] = os.path.expanduser(s)
        # hack for cd to behave like shell cd and stay in the directory
        if split_string[0] == 'cd':
            plumbum.local.cwd.chdir(split_string[1])
        else:
            cmd = plumbum.local[split_string[0]]
            for i in split_string[1:]:
                cmd = cmd[i]
            # log the invocation
            log_string = settings.COMMAND_LOG_STRING.format(cmd=cmd)
            if log_as_info:
                logger.info(log_string)
            else:
                logger.debug(log_string)

            # actually invoke the command
            if fg:
                cmd & plumbum.FG
            else:
                cmd()

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
    def error_if_path_exists(cls, path):
        path_exists = cls.path_exists(path)
        msg = None
        if path_exists:
            msg = 'Path "{0}" exists.'.format(path.strip())
            logger.error(msg)
        return msg

    @classmethod
    def path_exists(cls, path):
        try:
            return ls(path)
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
