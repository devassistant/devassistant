import plumbum
from plumbum.cmd import sudo

class RPMHelper(object):
    rpm = plumbum.local['rpm']

    @classmethod
    def is_rpm_present(cls, rpm_name):
        try:
            cls.rpm('-q', rpm_name)
            return True
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
