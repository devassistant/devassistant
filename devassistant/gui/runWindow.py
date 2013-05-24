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
from devassistant.gui.logger_gui import logger_gui
from devassistant.logger import logger
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from devassistant import path_runner
from devassistant import exceptions

GLib.threads_init()

class RunLoggingHandler(logging.Handler):
    def __init__(self, textbuffer):
        logging.Handler.__init__(self)
        self.textbuffer = textbuffer

    def utf8conv(self,x):
        try:
            return unicode(x,'utf8')
        except:
            return x

    def emit(self, record):
        it = self.textbuffer.get_end_iter()
        #self.textbuffer.place_cursor(it)
        self.textbuffer.insert(it,record.getMessage(),-1)

class runWindow(object):
    def __init__(self,  parent, finalWindow, builder, assistant):
        self.parent = parent
        self.finalWindow = finalWindow
        self.runWindow = builder.get_object("runWindow")
        self.textViewLog = builder.get_object("textViewLog")
        self.textbuffer = self.textViewLog.get_buffer()
        self.textViewLog.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.assistant = assistant
        self.tlh = RunLoggingHandler(self.textbuffer)
        logger.addHandler(self.tlh)
        FORMAT = "%(levelname)s %(message)s"
        self.tlh.setFormatter(logging.Formatter(FORMAT))
        logger.setLevel(logging.INFO)

    def open_window(self, widget, data=None):
        dirname, projectname = self.parent.pathWindow.get_data()
        self.runWindow.show_all()


    def visibility_event(self, widget, data=None):
        logger_gui.info("ListView Visibility event")
        thread = threading.Thread(target=self.devassistant_start)
        thread.start()

    def devassistant_start(self):
        logger_gui.info("Thread run")
        path = self.assistant.get_selected_subassistant_path(**self.parent.kwargs)
        pr = path_runner.PathRunner(path, self.parent.kwargs)
        try:
            pr.run()
        except exceptions.ExecutionException as ex:
            pass
