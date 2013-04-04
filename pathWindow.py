# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import mainWindow
import finalWindow
import logging
from gi.repository import Gtk

class pathWindow(object):
    def __init__(self, parent, mainWin, builder):
        self.parent = parent
        self.mainWin = mainWin
        self.pathWindow = builder.get_object("pathWindow")
        self.labelProjectName = builder.get_object("labelProjectName")
        self.builder = builder
        
    def nextWindow(self, widget, data=None):
        self.parent.finalWindow.openWindow(widget, data)
        self.pathWindow.hide()
        logging.info("nextWindow")
        
    def openWindow(self, widget, data=None):
        logging.info("Prev window")
        self.pathWindow.show_all()
   
    def prevWindow(self, widget, data=None):
        self.pathWindow.hide()
        self.parent.openWindow(widget, data)
        
    def browsePath(self, window):
        dialog = Gtk.FileChooserDialog(
            "Please choose directory", self.pathWindow,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
            )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.labelProjectName.set_text(dialog.get_filename())
        dialog.destroy()
        