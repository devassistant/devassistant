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
    def run_command(cls, cmd_str, fg=False, log_level=logging.DEBUG, realtime_output=False):
        """Runs a command from string, e.g. "cp foo bar" """
        if fg and realtime_output:
            # realtime output only makes sense with logging (fg command is realtime automatically)
            raise ValueError('Cannot use both realtime_output and fg.')

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
        stderr_pipe = None if fg else subprocess.PIPE if not realtime_output else subprocess.STDOUT
        proc = subprocess.Popen(cmd_str,
                                stdin=stdin_pipe,
                                stdout=stdout_pipe,
                                stderr=stderr_pipe,
                                shell=True)
        if realtime_output:
            stdout = []
            stderr = ''
            while proc.poll() == None:
                output = proc.stdout.readline().strip().decode('utf8')
                stdout.append(output)
                logger.log(log_level, settings.COMMAND_OUTPUT_STRING.format(line=output))
            stdout = '\n'.join(stdout)
            stderr = ''
        else:
            # decode because of Python 3
            stdout, stderr = map(lambda x: x.strip().decode('utf8') if x else '', proc.communicate())
            loggable_stdout = '\n'.join(map(lambda ln: settings.COMMAND_OUTPUT_STRING.format(line=ln),
                                            stdout.splitlines()))
            loggable_stderr = '\n'.join(map(lambda ln: settings.COMMAND_OUTPUT_STRING.format(line=ln),
                                            stderr.splitlines()))
            if not fg:
                if stdout:
                    logger.log(log_level, loggable_stdout)
                if stderr:
                    logger.log(log_level, loggable_stderr)

        if proc.returncode == 0:
            return stdout.strip()
        else:
            raise exceptions.ClException(cmd_str,
                                         proc.returncode,
                                         stdout,
                                         stderr if not fg else 'See command output above.')

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
    def resolve(cls, *args):
        logger.info('Resolving dependencies ...')
        import yum
        y = yum.YumBase()
        for arg in args:
            if arg.startswith('@'):
                y.selectGroup(arg[1:])
            else:
                pkg = y.returnPackageByDep(arg)
                y.install(pkg)
        y.resolveDeps()
        logger.info('Installing/Updating:')
        to_install = []
        for pkg in y.tsInfo.getMembers():
            to_install.append(pkg.po.ui_envra)
            logger.info(pkg.po.ui_envra)

        return to_install

    @classmethod
    def install(cls, *args):
        to_install = cls.resolve(*args)
        try:
            # Python 2 compat
            input = raw_input
        except NameError:
            pass
        yes = input('Is this ok? [y/n]: ')
        while not yes.lower()[0] in ['y', 'n']:
            yes = input('Wrong choice. Please choose from [y/n]: ')
        if yes.lower()[0] != 'y':
            return False

        cmd = ['pkexec', cls.c_yum, '-y', 'install']
        quoted_pkgs = map(lambda pkg: '"{pkg}"'.format(pkg=pkg), to_install)
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), log_level=logging.INFO, realtime_output=True)
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
