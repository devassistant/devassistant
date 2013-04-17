#!/usr/bin/env python
import sys

from gi.repository import Gtk

from devassistant import assistant_base
from devassistant import yaml_assistant_loader
from devassistant.logger import logging

import pathWindow
import finalWindow
import runWindow

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
        self.runWindow = runWindow.runWindow(self, self.finalWindow, self.builder, DevelAssistants())
        self.mainhandlers = {
                    "on_nextMainBtn_clicked": self.next_window,
                    "on_cancelMainBtn_clicked": Gtk.main_quit,
                    "on_mainWindow_delete_event": Gtk.main_quit,
                    "on_browsePathBtn_clicked": self.pathWindow.browse_path,
                    "on_cancelPathBtn_clicked": Gtk.main_quit,
                    "on_cancelFinalBtn_clicked": Gtk.main_quit,
                    "on_cancelRunBtn_clicked": Gtk.main_quit,
                    "on_nextPathBtn_clicked": self.pathWindow.next_window,
                    "on_pathWindow_delete_event": Gtk.main_quit,
                    "on_finalWindow_delete_event": Gtk.main_quit,
                    "on_runWindow_delete_event": Gtk.main_quit,
                    "on_prevPathBtn_clicked": self.pathWindow.prev_window,
                    "on_prevFinalBtn_clicked": self.finalWindow.prev_window,
                    "on_runFinalBtn_clicked": self.finalWindow.run_btn,
                    "on_store_list_selection_changed": self.store_view_cursor_changed,
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
        self.kwargs = {}
        k = 0
        for ass in self.subas:
            self.store.append([ass[0].fullname])
            if k == 0:
                if not ass[1]:
                    self.labelMainWindow.hide()
                    self.sublistView.hide()
                else:
                    for sub in ass[1]:
                        logging.info("subas:%s and %s" % (sub[0].name, sub[0].fullname))
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

    def browse_path(self, window):
        self.pathWindow.browsePath()

    def next_window(self, widget, data=None):
        logging.info("Next window")
        selection = self.listView.get_selection()
        subselection = self.sublistView.get_selection()
        model, path_list = selection.get_selected()
        submodel, subpath_list = subselection.get_selected()
        if path_list != None:
            tool = model[path_list][0]
            if tool in map(lambda x: x[0].fullname, self.subas):
                for ass in self.subas:
                    logging.info("Assistant:{0}".format(ass[0].fullname))
                    if tool == ass[0].fullname:
                        if not ass[1]:
                            logging.info("All is OK, we can go to the next screen")
                            self.kwargs['subassistant_0']=ass[0].name
                            if self.kwargs.has_key('sub_assistant_1') == True:
                                del (self.kwargs['sub_assistnant_1'])
                            self.pathWindow.open_window(widget, data=None)
                            self.mainWin.hide()
                        else:
                            logging.info(subpath_list)
                            if subpath_list == None:
                                logging.info("No subassistant have been selected")
                                md=Gtk.MessageDialog(None,
                                                     Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                                     Gtk.MessageType.WARNING,
                                                     Gtk.ButtonsType.CLOSE,
                                                     "Select one subassistant")
                                md.run()
                                md.destroy()
                            else:
                                subtool = submodel[subpath_list][0]
                                for sub in ass[1]:
                                    if subtool == sub[0].fullname:
                                        self.kwargs['subassistant_0']=ass[0].name
                                        self.kwargs['subassistant_1']=sub[0].name
                                        self.pathWindow.open_window(widget, data=None)
                                        self.mainWin.hide()

    def open_window(self, widget, data=None):
        logging.info("Prev window")
        self.mainWin.show_all()

    def cancel_window(self, widget):
        logging.info("Cancel window")

    def store_view_cursor_changed(self, selection):
        (model, path_list) = selection.get_selected()
        self.substore.clear()
        if path_list != None:
            tool = model[path_list][0]
            if tool in map(lambda x: x[0].fullname, self.subas):
                logging.info(type(self.subas))
                subassistant = self.subas.get_subassistant_chain()
                logging.info(subassistant)
                for ass in self.subas:
                    if tool == ass[0].fullname:
                        if not ass[1]:
                            self.labelMainWindow.hide()
                            self.sublistView.hide()
                        else:
                            for sub in ass[1]:
                                self.labelMainWindow.show_all()
                                self.sublistView.show_all()
                                self.substore.append([sub[0].fullname])
            else:
                self.labelMainWindow.hide()
                self.sublistView.hide()
