import logging
import os
import subprocess
import sys
import threading

from devassistant import exceptions
from devassistant import settings
from devassistant.logger import logger

class ClHelper(object):
    @classmethod
    def run_command(cls, cmd_str, fg=False, log_level=logging.DEBUG):
        """Runs a command from string, e.g. "cp foo bar" """
        formatted_string = settings.COMMAND_LOG_STRING.format(cmd=cmd_str)
        if fg:
            print(formatted_string)
        logger.log(log_level, formatted_string)

        if cmd_str.startswith('cd '):
            # special-case cd to behave like shell cd and stay in the directory
            try:
                # delete any qoutes, the quoting is automatical in os.chdir
                directory = cmd_str.split()[1].replace('"', '').replace('\'', '')
                os.chdir(directory)
            except OSError as e:
                raise exceptions.ClException(cmd_str, 1, '', str(e))
            return ''

        stdin_pipe = None
        stdout_pipe = None if fg else subprocess.PIPE
        stderr_pipe = None if fg else subprocess.PIPE
        proc = subprocess.Popen(cmd_str, stdin=stdin_pipe, stdout=stdout_pipe, stderr=stderr_pipe, shell=True)
        # decode because of Python 3
        # str because of Python 2, so that it doesn't print u'foo', but just 'foo'
        stdout, stderr = map(lambda x: x.strip().decode('utf8') if x else '', proc.communicate())
        loggable_stdout = '\n'.join(map(lambda line: settings.COMMAND_OUTPUT_STRING.format(line=line), stdout.splitlines()))
        loggable_stderr = '\n'.join(map(lambda line: settings.COMMAND_OUTPUT_STRING.format(line=line), stderr.splitlines()))
        if not fg:
            if stdout:
                logger.log(log_level, loggable_stdout)
            if stderr:
                logger.log(log_level, loggable_stderr)

        if proc.returncode == 0:
            return stdout.strip()
        else:
            raise exceptions.ClException(cmd_str, proc.returncode, stdout, stderr if not fg else 'See command output above.')

class RPMHelper(object):
    c_rpm = 'rpm'

    @classmethod
    def rpm_q(cls, rpm_name):
        try:
            # if we install by e.g. virtual provide, then rpm -q foo will fail
            # therefore we always use rpm -q --whatprovides foo
            return ClHelper.run_command(' '.join([cls.c_rpm, '-q', '--whatprovides', rpm_name.strip()]))
        except exceptions.ClException:
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
    c_yum = 'yum'

    @classmethod
    def install(cls, *args):
        cmd = ['pkexec', cls.c_yum, 'install']
        quoted_args = map(lambda arg: '"{arg}"'.format(arg=arg) if '(' in arg else arg, args)
        cmd.extend(quoted_args)
        logger.info('Installing: {0}'.format(', '.join(args)))
        try:
            ClHelper.run_command(' '.join(cmd), fg=True, log_level=logging.INFO)
            return args
        except exceptions.ClException:
            return False

    @classmethod
    def is_group_installed(cls, group):
        logger.info('Checking for presence of group {0}...'.format(group))

        output = ClHelper.run_command(' '.join([cls.c_yum, 'group', 'list', '"{0}"'.format(group)]))
        if 'Installed Groups' in output:
            logger.info('Found %s', group)
            return True

        logger.info('Not found')
        return False

class PathHelper(object):
    c_cp = 'cp'
    c_mkdir = 'mkdir'

    @classmethod
    def path_exists(cls, path):
        try:
            return ls(path).strip()
        except exceptions.ClException:
            return False

    @classmethod
    def mkdir_p(cls, path):
        try:
            return ClHelper.run_command(' '.join([cls.c_mkdir, '-p', path]))
        except exceptions.ClException:
            return False

    @classmethod
    def cp(cls, src, dest):
        try:
            return ClHelper.run_command(' '.join([cls.c_cp, src, dest]))
        except exceptions.ClException:
            return False
