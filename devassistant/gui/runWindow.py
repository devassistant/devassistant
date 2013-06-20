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
        #print "MSG:%s." % msg
        Gdk.threads_enter()
        if record.levelname == "INFO":
            # Create a new root tree element
            treeStore.append(None, [msg])
        else:
            # Append a new element in tree element
            if msg is not "":
                treeStore.append(lastRow, [msg])
        Gdk.threads_leave()

class runWindow(object):
    def __init__(self,  parent, finalWindow, builder, assistant):
        self.parent = parent
        self.finalWindow = finalWindow
        self.runWindow = builder.get_object("runWindow")
        self.runTreeView = builder.get_object("runTreeView")
        self.cancelBtn = builder.get_object("cancelRunBtn")
        self.assistant = assistant
        self.tlh = RunLoggingHandler(self.runTreeView)
        logger.addHandler(self.tlh)
        FORMAT = "%(levelname)s %(message)s"
        self.tlh.setFormatter(logging.Formatter(FORMAT))
        logger.setLevel(logging.DEBUG)
        self.store = Gtk.TreeStore(str)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Log from current process", renderer, text=0)
        self.runTreeView.append_column(column)
        self.runTreeView.set_model(self.store)

    def open_window(self, widget, data=None):
        dirname, projectname = self.parent.pathWindow.get_data()
        self.thread = threading.Thread(target=self.devassistant_start)
        self.runWindow.show_all()
        self.cancelBtn.set_sensitive(False)
        self.thread.start()
        self.cancelBtn.set_sensitive(True)

    def visibility_event(self, widget, data=None):
        logger_gui.info("ListView Visibility event")

    def check_thread(self):
        while self.thread.isAlive():
            time.sleep(1)
        self.cancelBtn.set_label("Close")

    def done_thread(self):
        self.cancelBtn.set_label("Close")
        return False

    def close_btn(self, widget, data=None):
        name = self.cancelBtn.get_label()
        if name == "Cancel":
            print "Cancelling thread"
            self.thread.stop()
        else:
            print "Quit dialog"
            Gtk.main_quit()

    def devassistant_start(self):
        logger_gui.info("Thread run")
        path = self.assistant.get_selected_subassistant_path(**self.parent.kwargs)
        pr = path_runner.PathRunner(path, self.parent.kwargs)
        try:
            pr.run()
            Gdk.threads_enter()
            self.cancelBtn.set_label("Close")
            Gdk.threads_leave()
        except exceptions.ExecutionException as ex:
            pass
