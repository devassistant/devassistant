from __future__ import print_function

import atexit
import getpass
import logging
import os
import signal
import subprocess
import sys

import six

from devassistant import current_run
from devassistant import exceptions
from devassistant.logger import logger


class ClHelper(object):
    command_processors = {}
    # register all invoked subprocesses
    subprocesses = {}

    @classmethod
    def run_command(cls,
                    cmd_str,
                    log_level=logging.DEBUG,
                    ignore_sigint=False,
                    output_callback=None,
                    as_user=None):
        """Runs a command from string, e.g. "cp foo bar"
        Args:
            cmd_str: the command to run as string
            log_level: level at which to log command output (DEBUG by default)
            ignore_sigint: should we ignore sigint during this command (False by default)
            output_callback: function that gets called with every line of output as argument
            as_user: run as specified user (the best way to do this will be deduced by DA)
                runs as current user if as_user == None
        """
        # run format processors on cmd_str
        for name, cmd_proc in cls.command_processors.items():
            cmd_str = cmd_proc(cmd_str)

        # TODO: how to do cd with as_user?
        if as_user and not cmd_str.startswith('cd '):
            cmd_str = cls.format_for_another_user(cmd_str, as_user)
        logger.log(log_level, cmd_str, extra={'event_type': 'cmd_call'})

        if cmd_str.startswith('cd '):
            # special-case cd to behave like shell cd and stay in the directory
            try:
                directory = cmd_str[3:]
                # delete any quotes, os.chdir doesn't split words like sh does
                if directory[0] == directory[-1] == '"':
                    directory = directory[1:-1]
                os.chdir(directory)
            except OSError as e:
                raise exceptions.ClException(cmd_str, 1, six.text_type(e))
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
        # register process to cls.subprocesses
        cls.subprocesses[proc.pid] = proc

        stdout = []
        while proc.poll() is None:
            output = proc.stdout.readline().decode('utf8')
            if output:
                output = output.strip()
                stdout.append(output)
                logger.log(log_level, output, extra={'event_type': 'cmd_out'})
            if output_callback:
                output_callback(output)

        # remove process from cls.subprocesses
        cls.subprocesses.pop(proc.pid)

        # add a newline to the end - if there is more output in output_rest, we'll be appending
        # it line by line; if there's no more output, we strip anyway
        stdout = '\n'.join(stdout) + '\n'
        # there may be some remains not read after exiting the previous loop
        output_rest = proc.stdout.read().strip().decode('utf8')
        # we want to log lines separately, not as one big chunk
        output_rest_lines = output_rest.splitlines()
        for i, l in enumerate(output_rest_lines):
            logger.log(log_level, l, extra={'event_type': 'cmd_out'})
            # add newline for every line - for last line, only add it if it was originally present
            if i != len(output_rest_lines) - 1 or output_rest.endswith('\n'):
                l += '\n'
            stdout += l
            if output_callback:
                output_callback(l)

        # log return code always on debug level
        logger.log(logging.DEBUG, proc.returncode, extra={'event_type': 'cmd_retcode'})
        stdout = stdout.strip()

        if proc.returncode == 0:
            return stdout
        else:
            raise exceptions.ClException(cmd_str,
                                         proc.returncode,
                                         stdout)

    @classmethod
    def format_for_another_user(cls, cmd_str, as_user):
        # TODO: implement the best way based on platform/other circumstances
        delimiter = 'DA_AS_USER_{0}'.format(as_user.upper())
        heredoc_firstline = ['pkexec']
        if as_user != 'root':
            heredoc_firstline.extend(['--user',  as_user])
        heredoc_firstline.append('bash << {delim}'.format(delim=delimiter))
        cmd = '\n'.join([' '.join(heredoc_firstline),
                         cmd_str,
                         delimiter
        ])
        return cmd

    @classmethod
    def ignore_sigint(cls):
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    @classmethod
    def kill_subprocesses(cls):
        for pid, proc in cls.subprocesses.items():
            logger.info('Killing still running process {pid} ...'.format(pid=pid))
            proc.kill()


atexit.register(ClHelper.kill_subprocesses)


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

    @classmethod
    def register_helper(cls, helper):
        """Decorator that appends a helper to list of helpers and then returns it."""
        cls.helpers[helper.shortname] = helper
        return helper

    @classmethod
    def get_appropriate_helper(cls):
        return cls.helpers[current_run.UI]

    @classmethod
    def ask_for_password(cls, prompt='Provide your password:', **options):
        """Returns the password typed by user as a string or None if user cancels the request
        (e.g. presses Ctrl + D on commandline or presses Cancel in GUI.
        """
        # optionally set title, that may be used by some helpers like zenity
        return cls.get_appropriate_helper().ask_for_password(prompt,
                                                             title=options.get('title', prompt))

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
        try:
            return getpass.getpass(prompt=prompt + ' ')
        except EOFError:
            return None

    @classmethod
    def _read_inp(cls):
        try:
            return cls.inp()
        except EOFError:
            return None

    @classmethod
    def ask_for_confirm_with_message(cls, prompt, message, **options):
        print(message)
        prompt += ' [y/n]'
        while True:
            print(prompt)
            choice = cls._read_inp()
            if choice is None:
                return None
            else:
                choice = choice.lower()
            if choice not in cls.yesno_list:
                print('You have to choose one of y/n.')
            else:
                return choice in cls.yes_list

    @classmethod
    def ask_for_package_list_confirm(cls, prompt, package_list, **options):
        prompt += ' [y(es)/n(o)/s(how)]: '
        while True:
            print(prompt, end='')
            choice = cls._read_inp()
            if choice is None:
                return None
            else:
                choice = choice.lower()
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
    show = True
    scrollwin = None
    info_btn = None

    @classmethod
    def get_gtk(cls):
        """
        Method sets cls.Gtk as a class parameter
        """
        if not cls.Gtk:
            try:
                from gi.repository import Gtk
                cls.Gtk = Gtk
            except ImportError:
                pass
        return cls.Gtk

    @classmethod
    def get_gdk(cls):
        """
        Method sets cls.Gdk as a class parameter
        """
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
    def _info_installed_packages(cls, win):
        def info_installed_packages(widget):
            if not cls.show:
                cls.scrollwin.hide()
                cls.show = True
                cls.info_btn.set_label("Show packages")
            else:
                cls.scrollwin.show_all()
                cls.show = False
                cls.info_btn.set_label("Hide packages")
        return info_installed_packages

    @classmethod
    def is_available(cls):
        return cls.get_gtk() is not None

    @classmethod
    def is_graphical(cls):
        return True

    @classmethod
    def _get_gtk_box(cls, win):
        box = win.get_content_area()
        box.set_margin_left(10)
        box.set_margin_right(10)
        return box

    @classmethod
    def _create_gtk_grid(cls, win):
        grid = cls.get_gtk().Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        return grid

    @classmethod
    def _create_yes_no(cls, win, yes="Yes", no="No"):
        yes_btn = cls._get_button(yes)
        yes_btn.connect('clicked', cls._ok_close(win))
        no_btn = cls._get_button(no)
        no_btn.connect('clicked', cls._cancel_close(win))
        return yes_btn, no_btn

    @classmethod
    def _create_list_store(cls, package_list):
        Gtk = cls.get_gtk()
        liststore = Gtk.ListStore(str)
        for pkg in sorted(package_list):
            liststore.append([pkg])
        listview = Gtk.TreeView(liststore)
        cell_renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("", cell_renderer, text=0)
        listview.set_headers_visible(False)
        listview.append_column(column)
        return listview

    @classmethod
    def _create_scrollwindow(cls):
        Gtk = cls.get_gtk()
        scrollwin = Gtk.ScrolledWindow()
        scrollwin.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        scrollwin.set_sensitive(True)
        scrollwin.set_hexpand(True)
        scrollwin.set_vexpand(True)
        return scrollwin

    @classmethod
    def ask_for_password(cls, prompt, **options):
        """
        Method shows password dialog
        """
        Gtk = cls.get_gtk()
        Gdk = cls.get_gdk()
        Gdk.threads_enter()
        win = Gtk.Dialog(title=prompt)
        win.ok = False

        box = cls._get_gtk_box(win)
        grid = cls._create_gtk_grid(win)
        box.add(grid)
        yes_btn, no_btn = cls._create_yes_no(win)
        pwd = cls._get_pwd_entry()

        grid.attach(pwd, 0, 0, 2, 1)
        grid.attach(no_btn, 0, 1, 1, 1)
        grid.attach(yes_btn, 1, 1, 1, 1)

        win.show_all()
        win.run()
        Gdk.threads_leave()
        return pwd.get_text() if win.ok else None

    @classmethod
    def ask_for_confirm_with_message(cls, prompt, message, **options):
        """
        Method shows a confirm message
        """
        Gtk = cls.get_gtk()
        Gdk = cls.get_gdk()
        Gdk.threads_enter()
        win = Gtk.Dialog(title=prompt)
        win.ok = False
        box = cls._get_gtk_box(win)
        grid = cls._create_gtk_grid(win)
        box.add(grid)
        yes_btn, no_btn = cls._create_yes_no(win)
        label = Gtk.Label(label=message)

        grid.attach(label, 0, 0, 2, 1)
        grid.attach(yes_btn, 0, 1, 1, 1)
        grid.attach(no_btn, 1, 1, 1, 1)

        win.show_all()
        win.run()
        Gdk.threads_leave()
        return win.ok

    @classmethod
    def ask_for_package_list_confirm(cls, prompt, package_list, **options):
        """
        Method shows a dialog with package list
        """
        Gtk = cls.get_gtk()
        Gdk = cls.get_gdk()
        Gdk.threads_enter()
        win = Gtk.Dialog('Dependencies Installation')
        win.set_default_size(200, 250)
        win.ok = False

        box = cls._get_gtk_box(win)
        grid = cls._create_gtk_grid(win)
        grid.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label(prompt)
        yes_btn, no_btn = cls._create_yes_no(win)
        cls.info_btn = cls._get_button('Show packages')
        cls.show = True
        cls.info_btn.connect('clicked', cls._info_installed_packages(win))

        listview = cls._create_list_store(package_list)
        cls.scrollwin = cls._create_scrollwindow()
        cls.scrollwin.add(listview)

        grid.attach(label, 0, 0, 3, 1)
        grid.attach(no_btn, 0, 1, 1, 1)
        grid.attach(yes_btn, 1, 1, 1, 1)
        grid.attach(cls.info_btn, 2, 1, 1, 1)
        grid.attach(cls.scrollwin, 0, 2, 3, 1)

        box.pack_start(grid, True, True, 10)
        win.show_all()
        # This needs to be after show_all
        # Otherwise ScrollWindow is shown always
        cls.scrollwin.hide()
        win.run()
        Gdk.threads_leave()
        return win.ok or None
