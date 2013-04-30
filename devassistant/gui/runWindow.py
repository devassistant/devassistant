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
        FORMAT = "%(asctime)s %(levelname)s %(message)s"
        self.tlh.setFormatter(logging.Formatter(FORMAT))
        logger.setLevel(logging.INFO)
        

    def open_window(self, widget, data=None):

        logger.info("main function")
        dirname, projectname = self.parent.pathWindow.get_data()
        logger.info("Dirname is: {0}/{1}".format(dirname,projectname))
        logger.info("Dirname2 is: {0}/{1}".format(dirname,projectname))
        logger.info("Dirname3 is: {0}/{1}".format(dirname,projectname))
        self.runWindow.show_all()


    def visibility_event(self, widget, data=None):
        logger.info("Visibility event")
        path = self.assistant.get_selected_subassistant_path(**self.parent.kwargs)
        pr = path_runner.PathRunner(path, self.parent.kwargs)
        try:
            pr.run()
        except exceptions.ExecutionException as ex:
            pass
