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
import threading
from devassistant.logger import logger
from gi.repository import Gtk
from devassistant import path_runner
from devassistant import exceptions

class RunLoggingHandler(logging.Handler):
    def __init__(self, textbuffer):
        logging.Handler.__init__(self)
        self.textbuffer = textbuffer

    def emit(self, record):
        text_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(text_iter,"{0}\n".format(record.getMessage()))

class ThreadDevAssistantClass(threading.Thread):
    def __init__(self, runWin):
        threading.Thread.__init__(self)
        self.runWin = runWin

    def run(self):
        self.tlh = RunLoggingHandler(self.runWin.textbuffer)
        logger.addHandler(self.tlh)
        path = self.runWin.assistant.get_selected_subassistant_path(**self.runWin.parent.kwargs)
        pr = path_runner.PathRunner(path, self.runWin.parent.kwargs)
        try:
            pr.run()
        except exceptions.ExecutionException as ex:
            pass


class runWindow(object):
    def __init__(self,  parent, finalWindow, builder, assistant):
        self.parent = parent
        self.finalWindow = finalWindow
        self.runWindow = builder.get_object("runWindow")
        self.textViewLog = builder.get_object("textViewLog")
        self.textbuffer = self.textViewLog.get_buffer()
        self.textViewLog.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.assistant = assistant
        

    def open_window(self, widget, data=None):

        dirname, projectname = self.parent.pathWindow.get_data()
        self.runWindow.show_all()


    def visibility_event(self, widget, data=None):
        logger.info("Visibility event")
        thread = ThreadDevAssistantClass(self)
        thread.start()

    def window_visibility_event(self, widget, data=None):
        logger.info("Visibility event")
        #thread = ThreadDevAssistantClass(self)
        #thread.start()

