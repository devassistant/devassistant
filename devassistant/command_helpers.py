import plumbum
from plumbum.cmd import ls, sudo

from devassistant.logger import logger

class RPMHelper(object):
    rpm = plumbum.local['rpm']

    @classmethod
    def rpm_q(cls, rpm_name):
        try:
            return cls.rpm('-q', rpm_name)
        except plumbum.ProcessExecutionError:
            return False

    @classmethod
    def is_rpm_present(cls, rpm_name):
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
    yum = plumbum.local['yum']

    @classmethod
    def install(cls, *args):
        cmd = cls.yum['-y', 'install'] #TODO: do we really want to assume yes?
        for arg in args:
            cmd = cmd[arg]
        sudo(cmd)

class PathHelper(object):
    cp = plumbum.local['cp']
    mkdir = plumbum.local['mkdir']

    @classmethod
    def error_if_path_exists(cls, path):
        path = cls.path_exists(path)
        msg = None
        if path:
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
    def make_dir(cls, path):
        try:
            return cls.mkdir('-p', path)
        except plumbum.ProcessExecutionError as e:
            print e
            return False

    @classmethod
    def copy(cls, src, dest):
        print src
        print dest
        try:
            return cls.cp(src, dest)
        except plumbum.ProcessExecutionError:
            return False
