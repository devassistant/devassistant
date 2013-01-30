import plumbum
from plumbum.cmd import ls, sudo

class RPMHelper(object):
    rpm = plumbum.local['rpm']

    @classmethod
    def is_rpm_present(cls, rpm_name):
        try:
            return cls.rpm('-q', rpm_name)
        except plumbum.ProcessExecutionError:
            return False

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
