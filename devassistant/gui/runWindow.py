# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import sys
import logging
import mainWindow
import pathWindow
import argparse
import threading, thread
import time
import locale
from devassistant.logger import logger
from devassistant.logger import logger_gui
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from devassistant import path_runner
from devassistant import exceptions
from devassistant.package_managers import DependencyInstaller
import gobject

class RunLoggingHandler(logging.Handler):
    def __init__(self, treeview):
        logging.Handler.__init__(self)
        self.treeview = treeview

    def utf8conv(self,x):
        try:
            return unicode(x,'utf8')
        except:
            return x

    def get_iter_last(self, model):
        itr = model.get_iter_first()
        last = None
        while itr:
            last = itr
            itr = model.iter_next(itr)
        return last

    def emit(self, record):
        msg = record.getMessage()
        treeStore = self.treeview.get_model()
        lastRow = self.get_iter_last(treeStore)
        Gdk.threads_enter()
        if not msg:
            # Message is empty and is not add to tree
            pass
        else:
            if record.levelname == "INFO":
                # Create a new root tree element
                treeStore.append(None, [msg])
            else:
                # Append a new element in tree element
                if not msg.startswith("|"):
                    treeStore.append(lastRow, [msg])
        Gdk.threads_leave()

class runWindow(object):
    def __init__(self,  parent, builder, gui_helper):
        self.parent = parent
        self.runWindow = builder.get_object("runWindow")
        self.runTreeView = builder.get_object("runTreeView")
        self.cancelBtn = builder.get_object("cancelRunBtn")
        self.infoBox = builder.get_object("infoBox")
        self.scrolledWindow = builder.get_object("scrolledWindow")
        self.tlh = RunLoggingHandler(self.runTreeView)
        self.gui_helper = gui_helper
        logger.addHandler(self.tlh)
        FORMAT = "%(levelname)s %(message)s"
        self.tlh.setFormatter(logging.Formatter(FORMAT))
        logger.setLevel(logging.DEBUG)
        self.store = Gtk.TreeStore(str)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Log from current process", renderer, text=0)
        self.runTreeView.append_column(column)
        self.runTreeView.set_model(self.store)
        self.thread = threading.Thread(target=self.devassistant_start)
        self.stop = threading.Event()
        self.pr = None
        self.link = self.gui_helper.create_button()

    def open_window(self, widget, data=None):
        dirname, projectname = self.parent.pathWindow.get_data()
        if self.parent.kwargs.get('github'):
            self.link = self.gui_helper.create_link_button(
                    "Link to project on Github",
                    "http://www.github.com/{0}/{1}".format(self.parent.kwargs.get('github'),projectname))
            self.link.set_border_width(6)
            self.link.set_sensitive(False)
            self.infoBox.pack_start(self.link, False, False, 12)
        self.runTreeView.connect('size-allocate', self.treeview_changed)
        self.runWindow.show_all()
        self.cancelBtn.set_sensitive(False)
        self.thread.start()
        self.cancelBtn.set_sensitive(True)
        self.link.set_sensitive(True)

    def done_thread(self):
        self.cancelBtn.set_label("Close")
        return False

    def close_btn(self, widget, data=None):
        name = self.cancelBtn.get_label()
        if name == "Cancel":
            dlg = self.gui_helper.create_message_dialog("Do you want to cancel project creation?",
                                                        buttons=Gtk.ButtonsType.YES_NO)
            response = dlg.run()
            if response == Gtk.ResponseType.YES:
                if self.thread.isAlive():
                    self.pr.stop()
                self.cancelBtn.set_label("Close")
            dlg.destroy()
        else:
            Gtk.main_quit()

    def treeview_changed(self, widget, event, data=None):
        adj = self.scrolledWindow.get_vadjustment()
        adj.set_value( adj.get_upper() - adj.get_page_size())

    def devassistant_start(self):
        #logger_gui.info("Thread run")
        #print self.parent.kwargs
        path = self.parent.assistant_class.get_selected_subassistant_path(**self.parent.kwargs)
        self.pr = path_runner.PathRunner(path, self.parent.kwargs)
        try:
            self.pr.run()
            Gdk.threads_enter()
            self.cancelBtn.set_label("Close")
            Gdk.threads_leave()
        except exceptions.ExecutionException:
            pass
