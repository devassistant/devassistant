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
    @classmethod
    def path_exists(cls, path):
        try:
            return ls(path)
        except plumbum.ProcessExecutionError:
            return False
