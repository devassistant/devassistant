# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import sys
import logging
import threading, thread
import time
import locale
import re
from devassistant.logger import logger
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from devassistant import path_runner
from devassistant import exceptions
from devassistant import sigint_handler


def get_iter_last(model):
    itr = model.get_iter_first()
    last = None
    while itr:
        last = itr
        itr = model.iter_next(itr)
    return last


def add_row(record, tree_store, last_row):
    tree_store.append(None, [record.getMessage()])

urlfinder = re.compile("(https?://[^\s<>\"]+|www\.[^\s<>\"]+)")

def switch_cursor(cursor_type, parent_window):
    watch = Gdk.Cursor(cursor_type)
    window = parent_window.get_root_window()
    window.set_cursor(watch)

class RunLoggingHandler(logging.Handler):
    def __init__(self, parent, treeview):
        logging.Handler.__init__(self)
        self.treeview = treeview
        self.parent = parent

    def utf8conv(self, x):
        try:
            return unicode(x, 'utf8')
        except:
            return x

    def emit(self, record):
        msg = record.getMessage()
        tree_store = self.treeview.get_model()
        last_row = get_iter_last(tree_store)
        Gdk.threads_enter()
        if msg:
            # Underline URLs in the record message
            msg = record.getMessage().replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            record.msg = urlfinder.sub(r'<u>\1</u>', msg)
            self.parent.debug_logs['logs'].append(record)
            # During execution if level is bigger then DEBUG
            # then GUI shows the message.
            if int(record.levelno) > 10 or self.parent.debugging:
                event_type = getattr(record, 'event_type', '')
                if event_type:
                    if event_type == 'dep_installation_start':
                        switch_cursor(Gdk.CursorType.WATCH, self.parent.run_window)
                    if event_type == 'dep_installation_end':
                        switch_cursor(Gdk.CursorType.ARROW, self.parent.run_window)
                if not event_type.startswith("dep_"):
                    add_row(record, tree_store, last_row)
        Gdk.threads_leave()


class RunWindow(object):
    def __init__(self,  parent, builder, gui_helper):
        self.parent = parent
        self.run_window = builder.get_object("runWindow")
        self.run_tree_view = builder.get_object("runTreeView")
        self.debug_btn = builder.get_object("debugBtn")
        self.info_box = builder.get_object("infoBox")
        self.scrolled_window = builder.get_object("scrolledWindow")
        self.back_btn = builder.get_object("backBtn")
        self.main_btn = builder.get_object("mainBtn")
        self.tlh = RunLoggingHandler(self, self.run_tree_view)
        self.gui_helper = gui_helper
        logger.addHandler(self.tlh)
        FORMAT = "%(levelname)s %(message)s"
        self.tlh.setFormatter(logging.Formatter(FORMAT))
        logger.setLevel(logging.DEBUG)
        self.store = Gtk.TreeStore(str)
        renderer = Gtk.CellRendererText()
        renderer.set_property('font', 'Liberation Mono')
        column = Gtk.TreeViewColumn("Log from current process", renderer, markup=0)
        self.run_tree_view.append_column(column)
        self.run_tree_view.set_model(self.store)
        self.run_tree_view.connect('row-activated', self.treeview_row_clicked)
        self.stop = threading.Event()
        self.pr = None
        self.debug_logs = dict()
        self.debug_logs['logs'] = list()
        self.link = self.gui_helper.create_button()
        self.info_label = gui_helper.create_label('<span color="#FFA500">In progress...</span>')
        self.info_box.pack_start(self.info_label, False, False, 12)
        self.project_canceled = False
        self.kwargs = {}
        self.current_main_assistant = None
        self.top_assistant = None
        self.close_win = False
        sigint_handler.override()

    def open_window(self, widget, data=None):
        if data is not None:
            self.kwargs = data.get('kwargs', None)
            self.top_assistant = data.get('top_assistant', None)
            self.current_main_assistant = data.get('current_main_assistant', None)
        self.store.clear()
        self.debug_logs = dict()
        self.debug_logs['logs'] = list()
        self.debugging = False
        self.thread = threading.Thread(target=self.devassistant_start)
        dirname, projectname = self.parent.path_window.get_data()
        if self.kwargs.get('github'):
            self.info_box.remove(self.link)
            self.link = self.gui_helper.create_link_button(
                    "Link to project on Github",
                    "http://www.github.com/{0}/{1}".format(self.kwargs.get('github'), projectname))
            self.link.set_border_width(6)
            self.link.set_sensitive(False)
            self.info_box.pack_start(self.link, False, False, 12)
        self.run_tree_view.connect('size-allocate', self.treeview_changed)
        self.run_window.show_all()
        self.disable_buttons()
        self.thread.start()

    def destroy(self, widget, data=None):
        Gtk.main_quit()

    def delete_event(self, widget, event, data=None):
        if not self.close_win:
            if self.thread.isAlive():
                dlg = self.gui_helper.create_message_dialog("Do you want to cancel project creation?",
                                                        buttons=Gtk.ButtonsType.YES_NO)
                response = dlg.run()
                if response == Gtk.ResponseType.YES:
                    if self.thread.isAlive():
                        self.info_label.set_label('<span color="#FFA500">Cancelling...</span>')
                        self.pr.stop()
                        self.project_canceled = True
                    else:
                        self.info_label.set_label('<span color="#008000">Done</span>')
                    self.allow_close_window()
                dlg.destroy()
                return True
        else:
            return False

    def treeview_changed(self, widget, event, data=None):
        adj = self.scrolled_window.get_vadjustment()
        adj.set_value( adj.get_upper() - adj.get_page_size())

    def allow_close_window(self):
        self.close_win = True

    def disable_close_window(self):
        self.close_win = False

    def disable_buttons(self):
        self.main_btn.set_sensitive(False)
        self.back_btn.hide()
        self.info_label.set_label('<span color="#FFA500">In progress...</span>')
        self.disable_close_window()
        self.link.hide()

    def allow_buttons(self, message="", link=True, back=True):
        self.info_label.set_label(message)
        self.allow_close_window()
        if link:
            self.link.set_sensitive(True)
            self.link.show_all()
        if back:
            self.back_btn.show()
        self.debug_btn.set_sensitive(True)
        self.main_btn.set_sensitive(True)

    def devassistant_start(self):
        #logger_gui.info("Thread run")
        path = self.top_assistant.get_selected_subassistant_path(**self.kwargs)
        self.pr = path_runner.PathRunner(path)
        try:
            self.pr.run(**self.kwargs)
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
        except exceptions.ClException as cl:
            self.allow_buttons(back=True, link=False, message='<span color="#FF0000">Failed: {0}</span>'.
                               format(cl.message))
        except exceptions.ExecutionException as ee:
            self.allow_buttons(back=True, link=False, message='<span color="#FF0000">Failed: {0}</span>'.
                               format((ee.message[:50]+'...') if len(ee.message) > 50 else ee.message))
        except IOError as ie:
            self.allow_buttons(back=True, link=False, message='<span color="#FF0000">Failed: {0}</span>'.
                               format((ie.message[:50]+'...') if len(ie.message) > 50 else ie.message))

    def debug_btn_clicked(self, widget, data=None):
        self.store.clear()
        if not self.debugging:
            self.debugging = True
            self.debug_btn.set_label('Info logs')
        else:
            self.debugging = False
            self.debug_btn.set_label('Debug logs')
        for record in self.debug_logs['logs']:
            last_row = get_iter_last(self.store)
            if self.debugging:
                # Create a new root tree element
                if getattr(record, 'event_type', '') != "cmd_retcode":
                    self.store.append(None, [record.getMessage()])
            else:
                if int(record.levelno) > 10:
                    add_row(record, self.store, last_row)

    def clipboard_btn_clicked(self, widget, data=None):
        _clipboard_text = list()
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
        self.run_window.hide()
        data = {}
        data['back'] = True
        data['top_assistant'] = self.top_assistant
        data['current_main_assistant'] = self.current_main_assistant
        data['kwargs'] = self.kwargs
        self.parent.path_window.open_window(widget, data)


    def main_btn_clicked(self, widget, data=None):
        self.run_window.hide()
        self.parent.open_window(widget,data)

    def treeview_row_clicked(self, treeview, path, view_column):
        model = treeview.get_model()
        text = model[path][0]
        match = urlfinder.search(text)
        if match is not None:
            url = match.group(1)
            import webbrowser
            webbrowser.open(url)
