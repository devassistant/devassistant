from __future__ import print_function

import getpass
import logging
import os
import signal
import subprocess
import sys

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
    # can be set to something different from the respective UI frontend
    use_helper = 'cli'

    @classmethod
    def register_helper(cls, helper):
        """Decorator that appends a helper to list of helpers and then returns it."""
        cls.helpers[helper.shortname] = helper
        return helper

    @classmethod
    def get_appropriate_helper(cls):
        return cls.helpers[cls.use_helper]

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

    @classmethod
    def ask_for_package_list_confirm(cls,
                                     prompt='Do you want to install packages?',
                                     package_list=[],
                                     **options):
        return cls.get_appropriate_helper().ask_for_package_list_confirm(prompt,
                                                                         package_list,
                                                                         **options)

@DialogHelper.register_helper
class CliDialogHelper(object):
    shortname = 'cli'
    yes_list = ['y', 'yes']
    yesno_list = yes_list + ['n', 'no']

    if sys.version_info[0] < 3:
        inp = raw_input
    else:
        inp = input

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
        prompt += ' [y/n]'
        while True:
            print(prompt)
            choice = cls.inp().lower()
            if choice not in cls.yesno_list:
                print('You have to choose one of y/n.')
            else:
                return choice in cls.yes_list

    @classmethod
    def ask_for_package_list_confirm(cls, prompt, package_list, **options):
        prompt += ' [y(es)/n(o)/s(how)]: '
        while True:
            print(prompt, end='')
            choice = cls.inp().lower()
            if choice not in cls.yesno_list + ['s', 'show']:
                print('You have to choose one of y/n/s.')
            else:
                if choice in cls.yesno_list:
                    return choice in cls.yes_list
                else:
                    print('\n'.join(sorted(package_list)))

@DialogHelper.register_helper
class GtkDialogHelper(object):
    shortname = 'gtk'
    Gtk = None
    Gdk = None
    top_window = None

    @classmethod
    def get_gtk(cls):
        if not cls.Gtk:
            try:
                from gi.repository import Gtk
                cls.Gtk = Gtk
            except ImportError:
                pass
        return cls.Gtk

    @classmethod
    def get_gdk(cls):
        if not cls.Gdk:
            try:
                from gi.repository import Gdk
                cls.Gdk = Gdk
            except ImportError:
                pass
        return cls.Gdk

    @classmethod
    def _get_button(cls, label):
        return cls.get_gtk().Button(label=label)

    @classmethod
    def _get_pwd_entry(cls):
        entry = cls.get_gtk().Entry()
        entry.set_visibility(False)
        return entry

    @classmethod
    def _ok_close(cls, win):
        def ok_close(widget):
            win.ok = True
            win.hide()
        return ok_close

    @classmethod
    def _cancel_close(cls, win):
        def cancel_close(widget):
            win.ok = False
            win.hide()
        return cancel_close

    @classmethod
    def is_available(cls):
        return cls.get_gtk() != None

    @classmethod
    def is_graphical(cls):
        return True

    @classmethod
    def ask_for_password(cls, prompt, **options):
        Gtk = cls.get_gtk()
        Gdk = cls.get_gdk()
        Gdk.threads_enter()
        win = Gtk.Dialog(title=prompt)
        win.ok = False
        box = win.get_content_area()

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        box.add(grid)
        box.set_margin_left(10)
        box.set_margin_right(10)

        ok = cls._get_button('Ok')
        ok.connect('clicked', cls._ok_close(win))
        cancel = cls._get_button('Cancel')
        cancel.connect('clicked', cls._cancel_close(win))
        pwd = cls._get_pwd_entry()

        grid.attach(pwd, 0, 0, 2, 1)
        grid.attach(cancel, 0, 1, 1, 1)
        grid.attach(ok, 1, 1, 1, 1)

        win.show_all()
        win.run()
        Gdk.threads_leave()
        return False if not win.ok else pwd.get_text()

    @classmethod
    def ask_for_confirm_with_message(cls, prompt, message, **options):
        raise NotImplementedError()

    @classmethod
    def ask_for_package_list_confirm(cls, prompt, package_list, **options):
        Gtk = cls.get_gtk()
        Gdk = cls.get_gdk()
        Gdk.threads_enter()
        win = Gtk.Dialog('Dependencies Installation')
        win.set_default_size(200, 50)
        win.ok = False
        box = win.get_content_area()

        grid = Gtk.Grid()
        grid.set_halign(Gtk.Align.CENTER)
        #grid.set_size_request(300, 50)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        box.remove(box.get_children()[0])
        box.pack_end(grid, True, True, 0)
        box.set_margin_left(10)
        box.set_margin_right(10)

        label = Gtk.Label(prompt)
        ok = cls._get_button('Ok')
        ok.connect('clicked', cls._ok_close(win))
        cancel = cls._get_button('Cancel')
        cancel.connect('clicked', cls._cancel_close(win))

        grid.attach(label, 0, 0, 2, 1)
        grid.attach(cancel, 0, 1, 1, 1)
        grid.attach(ok, 1, 1, 1, 1)

        win.show_all()
        win.run()
        Gdk.threads_leave()
        return win.ok
