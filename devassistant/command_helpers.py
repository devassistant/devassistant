import argparse
import getpass
import logging
import os
import signal
import subprocess
import sys
import tempfile

from devassistant import argument
from devassistant import exceptions
from devassistant.logger import logger
from devassistant import settings

class ClHelper(object):
    @classmethod
    def run_command(cls, cmd_str, log_level=logging.DEBUG, scls=[], ignore_sigint=False):
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
        preexec_fn = cls.ignore_sigint if ignore_sigint else None
        proc = subprocess.Popen(cmd_str,
                                stdin=stdin_pipe,
                                stdout=stdout_pipe,
                                stderr=stderr_pipe,
                                shell=True,
                                preexec_fn=preexec_fn)
        stdout = []
        while proc.poll() == None:
            output = proc.stdout.readline().strip().decode('utf8')
            stdout.append(output)
            logger.log(log_level, output, extra={'event_type': 'cmd_out'})
        stdout = '\n'.join(stdout)
        # there may be some remains not read after exiting the previous loop
        output_rest = proc.stdout.read().strip().decode('utf8')
        if output_rest:
            logger.log(log_level, output_rest, extra={'event_type': 'cmd_out'})
            stdout += '\n' + output_rest

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

    @classmethod
    def ignore_sigint(cls):
        signal.signal(signal.SIGINT, signal.SIG_IGN)

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
    helpers = {}
    # this will be assigned if user overrides UI backend from commandline
    user_override_helper = None

    @classmethod
    def get_argparse_argument(cls):
        """Return argument for argparse, that contains the list of UI choices and has
        a proper action (which will set a proper attribute of DialogHelper).
        """
        help='Force a specific backend for UI dialogs: [{names}]'.format(names=', '.join(cls.helpers.keys()))
        class UIAction(argparse.Action):
            klass = cls

            def __call__(self, parser, namespace, values, option_string=None):
                cls.user_override_helper = values
                setattr(namespace, self.dest, values)

        arg = argument.Argument(settings.UI_FLAG[2:],
                                settings.UI_FLAG,
                                action=UIAction,
                                required=False,
                                help=help)

        return arg

    @classmethod
    def register_helper(cls, helper):
        """Decorator that appends a helper to list of helpers and then returns it."""
        cls.helpers[helper.shortname] = helper
        return helper

    @classmethod
    def get_appropriate_helper(cls):
        if cls.user_override_helper:
            return cls.helpers['user_override_helper']

        available = []
        for h in filter(lambda x: x.is_graphical() == ('DISPLAY' in os.environ), cls.helpers.values()):
            if h.is_available():
                available.append(h)

        # return always the same (the values traversing from dict above is not deterministic)
        # we may want to assign some sort of priority to be able to actively influence which
        # helper will be chosen
        return sorted(available)[0]

    @classmethod
    def ask_for_password(cls, prompt='Provide your password:', **options):
        """Returns the password typed by user as a string

        TODO: could this be a security problem?
        """
        # optionally set title, that may be used by some helpers like zenity
        return cls.get_appropriate_helper().ask_for_password(prompt, title=options.get('title', prompt))

    @classmethod
    def ask_for_confirm_with_message(cls, prompt='Do you agree?', message='', **options):
        """Returns True if user agrees, False otherwise"""
        return cls.get_appropriate_helper().ask_for_confirm_with_message(prompt, message)

@DialogHelper.register_helper
class TTYDialogHelper(object):
    shortname = 'tty'

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def is_graphical(cls):
        return False

    @classmethod
    def ask_for_password(cls, prompt, **options):
        return getpass.getpass(prompt=prompt + ' ')

    @classmethod
    def ask_for_confirm_with_message(cls, prompt, message, **options):
        print(prompt + '\n')
        print(message)
        if int(sys.version[0]) < 3:
            input = raw_input
        prompt += ' [y/n]'
        while True:
            print(prompt)
            choice = input().lower()
            if choice not in ['y', 'yes', 'n', 'no']:
                print('You have to write y/yes/n/no (can be in capitals)')
            else:
                return choice in ['y', 'yes']

@DialogHelper.register_helper
class ZenityDialogHelper(object):
    c_zenity_wrapper = 'zenity_wrapper.sh'
    c_zenity = 'zenity'
    shortname = c_zenity

    @classmethod
    def is_available(cls):
        return True if ClHelper.run_command('which {zenity}'.format(zenity=cls.c_zenity)) else False

    @classmethod
    def is_graphical(cls):
        return True

    @classmethod
    def ask_for_password(cls, prompt, **options):
        return cls._ask_for_custom_input('entry',
                                         {'title': options.get('title', prompt),
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

        lines_num = len(message.splitlines())
        height = 120 + lines_num * 30
        # zenity will limit the window to monitor height, so we don't need to check maximum
        output = cls._ask_for_custom_input('text-info',
                                           {'title': prompt,
                                            'filename': fname,
                                            'width': 500,
                                            'height': height})
        os.remove(fname)
        return output

    @classmethod
    def _ask_for_custom_input(cls, input_type, zenity_options):
        """This is internal helper method, do not use this from outside, rather write your own ask_* method.

        Note, that we can't pass **zenity_options (with the "**") because some option names contain
        dash, which would get interpreter as minus by Python - e.g. no-wrap=foo would be interpreted as "no minus wrap"."""
        zenity_wrapper = os.path.join(os.path.dirname(__file__), cls.c_zenity_wrapper)
        if os.path.isfile(zenity_wrapper) and os.access(zenity_wrapper,os.X_OK):
            cls.c_zenity_wrapper = zenity_wrapper
        else:
            cls.c_zenity_wrapper = cls.c_zenity
        cmd = '{zenity} --{input_type} {options}'.format(zenity=cls.c_zenity_wrapper,
                                                         input_type=input_type,
                                                         options=' '.join(map(lambda x: '--{k}="{v}"'.format(k=x[0], v=x[1]),
                                                                              zenity_options.items())))
        try:
            return ClHelper.run_command(cmd)
        except exceptions.ClException:
            return False
