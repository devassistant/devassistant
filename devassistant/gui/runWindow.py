# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import mainWindow
import pathWindow
import argparse
from devassistant.logger import logging
from gi.repository import Gtk
from devassistant import path_runner
from devassistant import exceptions

class runWindow(object):
    def __init__(self,  parent, finalWindow, builder, assistant):
        self.parent = parent
        self.finalWindow = finalWindow
        self.runWindow = builder.get_object("runWindow")
        self.textViewLog = builder.get_object("textViewLog")
        logging.info("This is used for creating projects etc.")
        self.textbuffer = self.textViewLog.get_buffer()
        self.textViewLog.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.assistant = assistant

    def open_window(self, widget, data=None):

        logging.info("main function")
        dirname, projectname = self.parent.pathWindow.get_data()
        self.textbuffer.set_text("Dirname is: {0}/{1}".format(dirname,projectname))
        text_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(text_iter,"Dirname2 is: {0}/{1}".format(dirname,projectname))
        text_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(text_iter,"Dirname3 is: {0}/{1}".format(dirname,projectname))
        self.runWindow.show_all()

        parser = argparse.ArgumentParser(description='developer assistant GUI parser')
        parser.parse_args(self.parent.kwargs)
        print(parser)
        path = self.assistant.get_selected_subassistant_path(**vars(parser))
        print(path)
        pr = path_runner.PathRunner(path, self.parent.kwargs)
        try:
            pr.run()
        except exceptions.ExecutionException as ex:
            pass
