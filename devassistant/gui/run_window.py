# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import logging
import threading
import re
import os
from devassistant.logger import logger
from gi.repository import Gtk
from gi.repository import Gdk
from devassistant import path_runner
from devassistant import exceptions
from devassistant import sigint_handler


def add_row(record, list_store):
    """
    Function adds row to list_store used by List View
    """
    list_store.append([record.getMessage()])


URL_FINDER = re.compile("(https?://[^\s<>\":]+|www\.[^\s<>\":]+)")


def switch_cursor(cursor_type, parent_window):
    """
    Functions switches the cursor to cursor type
    """
    watch = Gdk.Cursor(cursor_type)
    window = parent_window.get_root_window()
    window.set_cursor(watch)


class RunLoggingHandler(logging.Handler):
    """
    Class take cares about logging
    """
    def __init__(self, parent, list_view):
        logging.Handler.__init__(self)
        self.list_view = list_view
        self.parent = parent

    def emit(self, record):
        """
        Function inserts log messages to list_view
        """
        msg = record.getMessage()
        list_store = self.list_view.get_model()
        Gdk.threads_enter()
        if msg:
            # Underline URLs in the record message
            msg = record.getMessage().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            record.msg = URL_FINDER.sub(r'<u>\1</u>', msg)
            self.parent.debug_logs['logs'].append(record)
            # During execution if level is bigger then DEBUG
            # then GUI shows the message.
            event_type = getattr(record, 'event_type', '')
            if event_type:
                if event_type == 'dep_installation_start':
                    switch_cursor(Gdk.CursorType.WATCH, self.parent.run_window)
                    add_row(record, list_store)
                if event_type == 'dep_installation_end':
                    switch_cursor(Gdk.CursorType.ARROW, self.parent.run_window)
            if not self.parent.debugging:
                # We will show only INFO messages and messages who have no dep_ event_type
                if int(record.levelno) > 10:
                    if event_type == "dep_check" or event_type == "dep_found":
                        add_row(record, list_store)
                    elif not event_type.startswith("dep_"):
                        add_row(record, list_store)
            if self.parent.debugging:
                if event_type != "cmd_retcode":
                    add_row(record, list_store)
        Gdk.threads_leave()


class RunWindow(object):
    """
    Class shows run window and executes
    project creation
    """
    def __init__(self, parent, builder, gui_helper):
        self.parent = parent
        self.run_window = builder.get_object("runWindow")
        self.run_list_view = builder.get_object("runTreeView")
        self.debug_btn = builder.get_object("debugBtn")
        self.info_box = builder.get_object("infoBox")
        self.scrolled_window = builder.get_object("scrolledWindow")
        self.back_btn = builder.get_object("backBtn")
        self.main_btn = builder.get_object("mainBtn")
        self.tlh = RunLoggingHandler(self, self.run_list_view)
        self.gui_helper = gui_helper
        logger.addHandler(self.tlh)
        format_msg = "%(levelname)s %(message)s"
        self.tlh.setFormatter(logging.Formatter(format_msg))
        logger.setLevel(logging.DEBUG)
        self.store = Gtk.ListStore(str)
        renderer = Gtk.CellRendererText()
        renderer.set_property('font', 'Liberation Mono')
        renderer.set_property('wrap_width', 750)
        renderer.set_property('wrap_mode', Gtk.WrapMode.WORD)
        column = Gtk.TreeViewColumn("Log from current process", renderer, markup=0)
        self.run_list_view.append_column(column)
        self.run_list_view.set_model(self.store)
        self.run_list_view.connect('row-activated', self.list_view_row_clicked)
        self.stop = threading.Event()
        self.dev_assistant_runner = None
        self.debug_logs = dict()
        self.debug_logs['logs'] = []
        self.link = None
        self.info_label = gui_helper.create_label('<span color="#FFA500">In progress...</span>')
        self.info_box.pack_start(self.info_label, False, False, 12)
        self.project_canceled = False
        self.kwargs = {}
        self.current_main_assistant = None
        self.top_assistant = None
        self.close_win = False
        self.debugging = False
        self.thread = None
        sigint_handler.override()

    def open_window(self, widget, data=None):
        """
        Function opens the run window
        """
        if data is not None:
            self.kwargs = data.get('kwargs', None)
            self.top_assistant = data.get('top_assistant', None)
            self.current_main_assistant = data.get('current_main_assistant', None)
            self.debugging = data.get('debugging', False)
            if not self.debugging:
                self.debug_btn.set_label('Debug logs')
            else:
                self.debug_btn.set_label('Info logs')
        self.store.clear()
        self.debug_logs = dict()
        self.debug_logs['logs'] = list()
        self.thread = threading.Thread(target=self.dev_assistant_start)
        # We need only project name for github
        project_name = self.parent.path_window.get_data()[1]
        if self.kwargs.get('github'):
            self.link = self.gui_helper.create_link_button(
                "Link to project on Github",
                "http://www.github.com/{0}/{1}".format(self.kwargs.get('github'), project_name))
            self.link.set_border_width(6)
            self.link.set_sensitive(False)
            self.info_box.pack_start(self.link, False, False, 12)
        self.run_list_view.connect('size-allocate', self.list_view_changed)
        # We need to be in /home directory before each project creations
        os.chdir(os.path.expanduser('~'))
        self.run_window.show_all()
        self.disable_buttons()
        self.thread.start()

    def destroy(self, widget, data=None):
        """
        Function quits the DevAssistant GUI
        """
        Gtk.main_quit()

    def remove_link_button(self):
        """
        Function removes link button from Run Window
        """
        if self.link is not None:
            self.info_box.remove(self.link)
            self.link.destroy()
            self.link = None

    def delete_event(self, widget, event, data=None):
        """
        Event cancels the project creation
        """
        if not self.close_win:
            if self.thread.isAlive():
                dlg = self.gui_helper.create_message_dialog("Do you want to cancel project creation?",
                                                            buttons=Gtk.ButtonsType.YES_NO)
                response = dlg.run()
                if response == Gtk.ResponseType.YES:
                    if self.thread.isAlive():
                        self.info_label.set_label('<span color="#FFA500">Cancelling...</span>')
                        self.dev_assistant_runner.stop()
                        self.project_canceled = True
                    else:
                        self.info_label.set_label('<span color="#008000">Done</span>')
                    self.allow_close_window()
                dlg.destroy()
                return True
        else:
            return False

    def list_view_changed(self, widget, event, data=None):
        """
        Function shows last rows.
        """
        adj = self.scrolled_window.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def allow_close_window(self):
        """
        Function sets flag to true
        """
        self.close_win = True

    def disable_close_window(self):
        """
        Function sets flag
        """
        self.close_win = False

    def disable_buttons(self):
        """
        Function disables buttons
        """
        self.main_btn.set_sensitive(False)
        self.back_btn.hide()
        self.info_label.set_label('<span color="#FFA500">In progress...</span>')
        self.disable_close_window()
        if self.link is not None:
            self.link.hide()

    def allow_buttons(self, message="", link=True, back=True):
        """
        Function allows buttons
        """
        self.info_label.set_label(message)
        self.allow_close_window()
        if link and self.link is not None:
            self.link.set_sensitive(True)
            self.link.show_all()
        if back:
            self.back_btn.show()
        self.main_btn.set_sensitive(True)

    def dev_assistant_start(self):
        """
        Thread executes devassistant API.
        """
        #logger_gui.info("Thread run")
        path = self.top_assistant.get_selected_subassistant_path(**self.kwargs)
        self.dev_assistant_runner = path_runner.PathRunner(path)
        try:
            self.dev_assistant_runner.run(**self.kwargs)
            Gdk.threads_enter()
            if not self.project_canceled:
                message = '<span color="#008000">Done</span>'
                link = True
                back = False
            else:
                message = '<span color="#FF0000">Failed</span>'
                link = False
                back = True
            self.allow_buttons(message=message, link=link, back=back)
            Gdk.threads_leave()
        except exceptions.ClException as cle:
            self.allow_buttons(back=True, link=False,
                               message='<span color="#FF0000">Failed: {0}</span>'.
                               format(cle.message))
        except exceptions.ExecutionException as exe:
            self.allow_buttons(back=True, link=False,
                               message='<span color="#FF0000">Failed: {0}</span>'.
                               format((exe.message[:50] + '...') if len(exe.message) > 50 else exe.message))
        except IOError as ioe:
            self.allow_buttons(back=True, link=False,
                               message='<span color="#FF0000">Failed: {0}</span>'.
                               format((ioe.message[:50] + '...') if len(ioe.message) > 50 else ioe.message))

    def debug_btn_clicked(self, widget, data=None):
        """
        Event in case that debug button is pressed.
        """
        self.store.clear()
        self.thread = threading.Thread(target=self.logs_update)
        self.thread.start()

    def logs_update(self):
        """
        Function updates logs.
        """
        Gdk.threads_enter()
        if not self.debugging:
            self.debugging = True
            self.debug_btn.set_label('Info logs')
        else:
            self.debugging = False
            self.debug_btn.set_label('Debug logs')
        for record in self.debug_logs['logs']:
            if self.debugging:
                # Create a new root tree element
                if getattr(record, 'event_type', '') != "cmd_retcode":
                    self.store.append([record.getMessage()])
            else:
                if int(record.levelno) > 10:
                    self.store.append([record.getMessage()])
        Gdk.threads_leave()

    def clipboard_btn_clicked(self, widget, data=None):
        """
        Function copies logs to clipboard.
        """
        _clipboard_text = []
        for record in self.debug_logs['logs']:
            if self.debugging:
                _clipboard_text.append(record.getMessage())
            else:
                if int(record.levelno) > 10:
                    if getattr(record, 'event_type', ''):
                        if not record.event_type.startswith("dep_"):
                            _clipboard_text.append(record.getMessage())
                    else:
                        _clipboard_text.append(record.getMessage())
        self.gui_helper.create_clipboard(_clipboard_text)

    def back_btn_clicked(self, widget, data=None):
        """
        Event for back button.
        This occurs in case of devassistant fail.
        """
        self.remove_link_button()
        self.run_window.hide()
        data = dict()
        data['back'] = True
        data['top_assistant'] = self.top_assistant
        data['current_main_assistant'] = self.current_main_assistant
        data['kwargs'] = self.kwargs
        self.parent.path_window.open_window(widget, data)

    def main_btn_clicked(self, widget, data=None):
        """
        Button switches to Dev Assistant GUI main window
        """
        self.remove_link_button()
        data = dict()
        data['debugging'] = self.debugging
        self.run_window.hide()
        self.parent.open_window(widget, data)

    def list_view_row_clicked(self, list_view, path, view_column):
        """
        Function opens the firefox window with relevant link
        """
        model = list_view.get_model()
        text = model[path][0]
        match = URL_FINDER.search(text)
        if match is not None:
            url = match.group(1)
            import webbrowser

            webbrowser.open(url)
