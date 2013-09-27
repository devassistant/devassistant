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
from devassistant.logger import logger
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from devassistant import path_runner
from devassistant import exceptions

def get_iter_last(model):
    itr = model.get_iter_first()
    last = None
    while itr:
        last = itr
        itr = model.iter_next(itr)
    return last

def add_row(record, tree_store, last_row):
    if record.levelname == "INFO":
        # Create a new root tree element
        tree_store.append(None, [record.getMessage()])
    else:
        # Append a new element in tree element
        if not record.getMessage().startswith("|"):
            tree_store.append(last_row, [record.getMessage()])

class RunLoggingHandler(logging.Handler):
    def __init__(self, parent, treeview):
        logging.Handler.__init__(self)
        self.treeview = treeview
        self.parent = parent


    def utf8conv(self,x):
        try:
            return unicode(x,'utf8')
        except:
            return x


    def emit(self, record):
        msg = record.getMessage()
        tree_store = self.treeview.get_model()
        last_row = get_iter_last(tree_store)
        Gdk.threads_enter()
        if not msg:
            # Message is empty and is not add to tree
            pass
        else:
            self.parent.debug_logs['logs'].append(record)
            if record.levelname != 'DEBUG':
                if getattr(record,'event_type',''):
                    if not record.event_type.startswith("dep_"):
                        add_row(record, tree_store, last_row)
                else:
                    add_row(record, tree_store, last_row)
        Gdk.threads_leave()

class RunWindow(object):
    def __init__(self,  parent, builder, gui_helper):
        self.parent = parent
        self.run_window = builder.get_object("runWindow")
        self.run_tree_view = builder.get_object("runTreeView")
        self.cancel_btn = builder.get_object("cancelRunBtn")
        self.debug_btn = builder.get_object("debugBtn")
        self.info_box = builder.get_object("infoBox")
        self.scrolled_window = builder.get_object("scrolledWindow")
        self.tlh = RunLoggingHandler(self, self.run_tree_view)
        self.gui_helper = gui_helper
        logger.addHandler(self.tlh)
        FORMAT = "%(levelname)s %(message)s"
        self.tlh.setFormatter(logging.Formatter(FORMAT))
        logger.setLevel(logging.DEBUG)
        self.store = Gtk.TreeStore(str)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Log from current process", renderer, text=0)
        self.run_tree_view.append_column(column)
        self.run_tree_view.set_model(self.store)
        self.thread = threading.Thread(target=self.devassistant_start)
        self.stop = threading.Event()
        self.pr = None
        self.link = self.gui_helper.create_button()
        self.info_label = gui_helper.create_label('<span color="#FFA500">In progress...</span>')
        self.project_canceled = False
        self.debugging = False
        self.debug_logs = dict()
        self.debug_logs['logs'] = list()

    def open_window(self, widget, data=None):
        dirname, projectname = self.parent.path_window.get_data()
        self.info_box.pack_start(self.info_label, False, False, 12)
        if self.parent.kwargs.get('github'):
            self.link = self.gui_helper.create_link_button(
                    "Link to project on Github",
                    "http://www.github.com/{0}/{1}".format(self.parent.kwargs.get('github'),projectname))
            self.link.set_border_width(6)
            self.link.set_sensitive(False)
            self.info_box.pack_start(self.link, False, False, 12)
        self.run_tree_view.connect('size-allocate', self.treeview_changed)
        self.run_window.show_all()
        self.cancel_btn.set_sensitive(False)
        self.debug_btn.set_sensitive(False)
        self.thread.start()
        self.cancel_btn.set_sensitive(True)
        self.link.set_sensitive(True)

    def done_thread(self):
        self.cancel_btn.set_label("Close")
        return False

    def close_btn(self, widget, data=None):
        name = self.cancel_btn.get_label()
        if name == "Cancel":
            dlg = self.gui_helper.create_message_dialog("Do you want to cancel project creation?",
                                                        buttons=Gtk.ButtonsType.YES_NO)
            response = dlg.run()
            if response == Gtk.ResponseType.YES:
                if self.thread.isAlive():
                    self.info_label.set_label('<span color="#FFA500">Cancelling...</span>')
                    self.cancel_btn.set_sensitive(False)
                    self.pr.stop()
                    self.project_canceled = True
                else:
                    self.info_label.set_label('<span color="#008000">Done</span>')
                self.cancel_btn.set_label("Close")
            dlg.destroy()

        else:
            Gtk.main_quit()

    def treeview_changed(self, widget, event, data=None):
        adj = self.scrolled_window.get_vadjustment()
        adj.set_value( adj.get_upper() - adj.get_page_size())

    def devassistant_start(self):
        #logger_gui.info("Thread run")
        path = self.parent.assistant_class.get_selected_subassistant_path(**self.parent.kwargs)
        self.pr = path_runner.PathRunner(path)
        try:
            self.pr.run(**self.parent.kwargs)
            Gdk.threads_enter()
            if not self.project_canceled:
                self.info_label.set_label('<span color="#008000">Done</span>')
                self.cancel_btn.set_label("Close")
            else:
                self.cancel_btn.set_sensitive(True)
                self.info_label.set_label('<span color="#FF0000">Failed</span>')
            self.debug_btn.set_sensitive(True)
            Gdk.threads_leave()
        except exceptions.ClException as cl:
            self.debug_btn.set_sensitive(True)
            self.cancel_btn.set_label("Close")
            self.info_label.set_label('<span color="#FF0000">Failed: {0}</span>'.format(cl.message))
        except exceptions.ExecutionException as ee:
            self.debug_btn.set_sensitive(True)
            self.cancel_btn.set_label("Close")
            self.info_label.set_label('<span color="#FF0000">Failed: {0}</span>'.format((ee.message[:50]+'...') if len(ee.message) > 50 else ee.message))
        except IOError as ie:
            self.debug_btn.set_sensitive(True)
            self.cancel_btn.set_label("Close")
            self.info_label.set_label('<span color="#FF0000">Failed: {0}</span>'.format((ie.message[:50]+'...') if len(ie.message) > 50 else ie.message))

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
                if record.levelname == "INFO":
                    # Create a new root tree element
                    self.store.append(None, [record.getMessage()])
                else:
                    # Append a new element in tree element
                    if not record.getMessage().startswith("|"):
                        self.store.append(last_row, [record.getMessage()])
            else:
                if record.levelname != 'DEBUG':
                    if getattr(record,'event_type',''):
                        if not record.event_type.startswith("dep_"):
                            add_row(record, self.store, last_row)
                    else:
                        add_row(record, self.store, last_row)

