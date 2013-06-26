import logging
import os
import subprocess
import tempfile

from devassistant import exceptions
from devassistant.logger import logger

class ClHelper(object):
    @classmethod
    def run_command(cls, cmd_str, log_level=logging.DEBUG, scls=[]):
        """Runs a command from string, e.g. "cp foo bar" """

        # format for scl execution if needed
        cmd_str = cls.format_for_scls(cmd_str, scls)
        logger.log(log_level, cmd_str, extra={'event_type': 'cmd_call'})

        if cmd_str.startswith('cd '):
            # special-case cd to behave like shell cd and stay in the directory
            try:
                # delete any qoutes, the quoting is automatical in os.chdir
                directory = cmd_str.split()[1].replace('"', '').replace('\'', '')
                os.chdir(directory)
            except OSError as e:
                raise exceptions.ClException(cmd_str, 1, str(e))
            return ''

        stdin_pipe = None
        stdout_pipe = subprocess.PIPE
        stderr_pipe = subprocess.STDOUT
        proc = subprocess.Popen(cmd_str,
                                stdin=stdin_pipe,
                                stdout=stdout_pipe,
                                stderr=stderr_pipe,
                                shell=True)
        stdout = []
        while proc.poll() == None:
            output = proc.stdout.readline().strip().decode('utf8')
            stdout.append(output)
            logger.log(log_level, output, extra={'event_type': 'cmd_out'})
        stdout = '\n'.join(stdout) + proc.stdout.read().decode('utf8')

        if proc.returncode == 0:
            return stdout.strip()
        else:
            raise exceptions.ClException(cmd_str,
                                         proc.returncode,
                                         stdout)

    @classmethod
    def format_for_scls(cls, cmd_str, scls):
        if scls and not cmd_str.startswith('cd '):
            cmd_str = 'scl {scls} - << DA_SCL_EOF\n {cmd_str} \nDA_SCL_EOF'.format(cmd_str=cmd_str,
                                                                                   scls=' '.join(scls))
        return cmd_str

class RPMHelper(object):
    c_rpm = 'rpm'

    @classmethod
    def rpm_q(cls, rpm_name):
        try:
            # if we install by e.g. virtual provide, then rpm -q foo will fail
            # therefore we always use rpm -q --whatprovides foo
            return ClHelper.run_command(' '.join([cls.c_rpm,
                                                  '-q',
                                                  '--whatprovides',
                                                  '"' + rpm_name.strip() + '"']))
        except exceptions.ClException:
            return False

    @classmethod
    def is_rpm_installed(cls, rpm_name):
        logger.info('Checking for presence of {0}...'.format(rpm_name), extra={'event_type': 'dep_check'})

        found_rpm = cls.rpm_q(rpm_name)
        if found_rpm:
            logger.info('Found {0}'.format(found_rpm), extra={'event_type': 'dep_found'})
        else:
            logger.info('Not found, will install', extra={'event_type': 'dep_not_found'})
        return found_rpm

    @classmethod
    def was_rpm_installed(cls, rpm_name):
        # TODO: handle failure
        found_rpm = cls.rpm_q(rpm_name)
        logger.info('Installed {0}'.format(found_rpm), extra={'event_type': 'dep_installed'})
        return found_rpm


class YUMHelper(object):
    c_yum = 'yum'

    @classmethod
    def resolve(cls, *args):
        logger.info('Resolving dependencies ...')
        import yum
        y = yum.YumBase()
        y.setCacheDir(tempfile.mkdtemp())
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
        ret = DialogHelper.ask_for_confirm_with_message(prompt='Install following packages?',
                                                        message='\n'.join(to_install))
        if ret is False:
            return False

        cmd = ['pkexec', cls.c_yum, '-y', 'install']
        quoted_pkgs = map(lambda pkg: '"{pkg}"'.format(pkg=pkg), to_install)
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), log_level=logging.INFO)
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
    c_test = 'test'

    @classmethod
    def path_exists(cls, path):
        try:
            return ClHelper.run_command(' '.join([cls.c_test, '-e', path])).strip()
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

class DialogHelper(object):
    """This class is to be used in all places where user interaction is required. It will
    decide on its own which specific helper it is best to use in this place (CommandLine,
    Zenity, possibly other registered).
    """
    helpers = []

    @classmethod
    def register_helper(cls, helper):
        """Decorator that appends a helper to list of helpers and then returns it."""
        cls.helpers.append(helper)
        return helper

    @classmethod
    def get_appropriate_helper(cls):
        return cls.helpers[1]

    @classmethod
    def ask_for_password(cls, prompt='Your password:', **options):
        """Returns the password typed by user as a string

        TODO: could this be a security problem?
        """
        return cls.get_appropriate_helper().ask_for_password(prompt)

    @classmethod
    def ask_for_confirm_with_message(cls, prompt='Do you agree?', message='', **options):
        """Returns True if user agrees, False otherwise"""
        return cls.get_appropriate_helper().ask_for_confirm_with_message(prompt, message)

@DialogHelper.register_helper
class TTYDialogHelper(object):
    for_tty = True
    for_xwindow = False

    @classmethod
    def ask_for_password(cls, prompt, **options):
        pass

    @classmethod
    def ask_for_confirm_with_message(cls, prompt, message, **options):
        pass

@DialogHelper.register_helper
class ZenityHelper(object):
    for_tty = False
    for_xwindow = True
    c_zenity = 'zenity'

    @classmethod
    def ask_for_password(cls, prompt, **options):
        return cls._ask_for_custom_input('entry',
                                         {'title': 'Provide your password',
                                          'text': prompt,
                                          'hide-text': ''})

    @classmethod
    def ask_for_confirm_with_message(cls, prompt, message, **options):
        # Zenity sucks for package list displaying, as it appends newline for every line with a dash
        # in question dialog. Therefore we write package names to temp file and use --text-info.
        # see https://bugzilla.gnome.org/show_bug.cgi?id=702752
        h, fname = tempfile.mkstemp()
        f = open(fname, 'w')
        f.write(message)
        f.close()

        # TODO: don't hardcode width and height
        output = cls._ask_for_custom_input('text-info',
                                           {'title': prompt,
                                            'filename': fname,
                                            'width': 500,
                                            'height': 600})
        os.remove(fname)
        return output

    @classmethod
    def _ask_for_custom_input(cls, input_type, zenity_options):
        """This is internal helper method, do not use this from outside, rather write your own ask_* method.

        Note, that we can't pass **zenity_options (with the "**") because some option names contain
        dash, which would get interpreter as minus by Python - e.g. no-wrap=foo would be interpreted as "no minus wrap"."""
        cmd = '{zenity} --{input_type} {options}'.format(zenity=cls.c_zenity,
                                                         input_type=input_type,
                                                         options=' '.join(map(lambda x: '--{k}="{v}"'.format(k=x[0], v=x[1]),
                                                                              zenity_options.items())))
        try:
            return ClHelper.run_command(cmd)
        except exceptions.ClException:
            return False
