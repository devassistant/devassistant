#!/usr/bin/env python
import logging
import sys

from gi.repository import Gtk

from devassistant import assistant_base
from devassistant import yaml_assistant_loader

import pathWindow
import finalWindow
logger = logging.getLogger()

console_handler = logging.StreamHandler(stream=sys.stdout)
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

gladefile = "./devel-assistant.glade"


class DevelAssistants(assistant_base.AssistantBase):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants()
        return sa


class mainWindow(object):

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.mainWin = self.builder.get_object("mainWindow")
        self.pathWindow = pathWindow.pathWindow(self, self.mainWin, self.builder)
        self.finalWindow = finalWindow.finalWindow(self, self.pathWindow, self.builder)
        self.mainhandlers = {
                    "on_nextMainBtn_clicked": self.nextWindow,
                    "on_cancelMainBtn_clicked": Gtk.main_quit,
                    "on_mainWindow_delete_event": Gtk.main_quit,
                    "on_storeView_row_activated": self.storeRowActivated,
                    "on_browsePathBtn_clicked": self.pathWindow.browsePath,
                    "on_cancelPathBtn_clicked": Gtk.main_quit,
                    "on_cancelFinalBtn_clicked": Gtk.main_quit,
                    "on_nextPathBtn_clicked": self.pathWindow.nextWindow,
                    "on_pathWindow_delete_event": Gtk.main_quit,
                    "on_finalWindow_delete_event": Gtk.main_quit,
                    "on_prevPathBtn_clicked": self.pathWindow.prevWindow,
                    "on_prevFinalBtn_clicked": self.finalWindow.prevWindow,
                    "on_runFinalBtn_clicked": self.finalWindow.runBtn,
                        }
        self.builder.connect_signals(self.mainhandlers)
        self.listView = self.builder.get_object("storeView")
        self.labelMainWindow = self.builder.get_object("sublabel")
        self.sublistView = self.builder.get_object("subStoreView")
        self.substoreList = self.builder.get_object("substoreList")
        self.labelProjectName = self.builder.get_object("labelProjectName")
        self.main, self.subas = DevelAssistants().get_subassistant_chain()
        self.store = Gtk.ListStore(str)
        self.substore = Gtk.ListStore(str)
        k = 0
        for ass in self.subas:
            self.store.append([ass[0].fullname])
            if k == 0:
                if not ass[1]:
                    self.labelMainWindow.hide()
                    self.sublistView.hide()
                else:
                    for sub in ass[1]:
                        logger.info("subas:%s and %s" % (sub[0].name, sub[0].fullname))
                        self.substore.append([sub[0].fullname])
                    self.labelMainWindow.show()
                    self.sublistView.show()
            k += 1

        self.listView.set_model(self.store)
        self.sublistView.set_model(self.substore)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("List of languages", renderer, text=0)
        self.listView.append_column(column)
        subrenderer = Gtk.CellRendererText()
        subcolumn = Gtk.TreeViewColumn("List of languages", subrenderer, text=0)
        self.sublistView.append_column(subcolumn)
        self.mainWin.show_all()
        Gtk.main()

    def browsePath(self, window):
        self.pathWindow.browsePath()
        
    def windowQuit(self, widget):
        Gtk.main_quit

    def nextWindow(self, widget, data=None):
        logger.info("Next window")
        self.pathWindow.openWindow(widget, data=None)
        self.mainWin.hide()

    def openWindow(self, widget, data=None):
        logger.info("Prev window")
        self.mainWin.show_all()

    def cancelWindow(self, widget):
        logger.info("Cancel window")

    def storeRowActivated(self, widget, row, col):
        logger.info("handler for switch betwenn tools")
        model = widget.get_model()
        self.substore.clear()
        tool = model[row][0]
        logger.info("tools is: {0}".format(tool))
        if tool in map(lambda x: x[0].fullname, self.subas):
            for ass in self.subas:
                logger.info(ass[0].fullname)
                if tool == ass[0].fullname:
                    for sub in ass[1]:
                        logger.info(sub[0].args[0].flags)
                        logger.info(sub[0].args[0].kwargs)
                        logger.info(sub[0].args[1].flags)
                        logger.info(sub[0].args[1].kwargs)
                        self.labelMainWindow.show_all()
                        self.sublistView.show_all()
                        self.substore.append([sub[0].fullname])
        else:
            self.labelMainWindow.hide()
            self.substore.hide()

 
    def runWizard(self, window):
        logger.info("Run wizard")
        name = self.labelProjectName.get_text()
        logger.info("Project name is: %s" % name)
