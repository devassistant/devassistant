# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import mainWindow
import pathWindow
import logging
from gi.repository import Gtk

class finalWindow(object):
    def __init__(self,  parent, pathWindow, builder):
        self.parent = parent
        self.pathWindow = pathWindow
        self.finalWindow = builder.get_object("finalWindow")
        self.boxFinal = builder.get_object("boxFinal")
        
    def prevWindow(self, widget, data=None):
        self.pathWindow.openWindow(widget, data)
        self.finalWindow.hide()

    def openWindow(self, widget, data=None):
        logging.info("Prev window")
        self.label = Gtk.Label("testing label")
        self.boxFinal.pack_start(self.label,False,False,0)
        for ass in self.parent.subas:
            logging.info(ass[0].fullname)
            logging.info(ass)
            for sub in ass[1]:
                logging.info(sub[0].fullname)
                for arg in sub[0].args:
                    if arg.flags[1] != '--name':
                        logging.info(arg.flags[1])
                        logging.info(arg.kwargs['help'])
        self.finalWindow.show_all()
    
    def runBtn(self, widget, data=None):
        logging.info("run button")
        logging.info(self.parent.main)
