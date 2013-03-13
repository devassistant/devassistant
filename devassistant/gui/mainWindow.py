#!/usr/bin/env python
import logging
import sys

from gi.repository import Gtk

from devassistant import assistant_base
from devassistant import yaml_assistant_loader
from devassistant.assistants import python

logger = logging.getLogger()

console_handler = logging.StreamHandler(stream=sys.stdout)
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

gladefile = "./devel-assistant.glade"

class DevelAssistants(assistant_base.AssistantBase):
    def get_subassistants(self):
        sa = [python.PythonAssistant]
        sa.extend(yaml_loader.YamlAssistantLoader.get_top_level_assistants())
        return sa
    
class mainWindow(Gtk.Window):
    
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file(gladefile)
        self.mainWin = builder.get_object("mainWindow")
        self.pathWin = builder.get_object("pathWindow")
        self.finalWin = builder.get_object("finalWindow")
        self.winNumber = 0
        handlers = {
                    "on_nextMainBtn_clicked": self.nextWindow,
                    "on_nextPathBtn_clicked": self.nextWindow,
                    "on_runFinalBtn_clicked": self.runWizard,
                    "on_prevPathBtn_clicked": self.prevWindow,
                    "on_prevFinalBtn_clicked": self.prevWindow,
                    "on_cancelMainBtn_clicked": Gtk.main_quit,
                    "on_cancelPathBtn_clicked": Gtk.main_quit,
                    "on_cancelFinalBtn_clicked": Gtk.main_quit,
                    "on_mainWindow_delete_event": Gtk.main_quit,
                    "on_pathWindow_delete_event": Gtk.main_quit,
                    "on_pathWindow_delete_event": Gtk.main_quit,
                    "on_storeView_row_activated": self.storeRowActivated,
                    "on_browsePathBtn_clicked": self.browsePath,
                        }
        builder.connect_signals(handlers)
        self.listView = builder.get_object("storeView")
        self.sublistView = builder.get_object("subStoreView")
        self.labelProjectName = builder.get_object("labelProjectName")
        self.main, self.subas= DevelAssistants().get_subassistant_chain()
        self.store = Gtk.ListStore(str)
        self.substore = Gtk.ListStore(str)
        logger.info("%s" % self.subas)
        k = 0
        for ass in self.subas:
            logger.info("%s and %s" % (ass[0].name, ass[0].fullname))
            self.store.append([ass[0].fullname])
            if k == 0:
                subas1 = ass[1]
                for sub in subas1:
                    logger.info("%s and %s" % (sub[0].name, sub[0].fullname))
                    self.substore.append([sub[0].fullname])
                
        self.listView.set_model(self.store)
        self.sublistView.set_model(self.substore)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("List of languages", renderer, text=0)
        self.listView.append_column(column)
        subrenderer = Gtk.CellRendererText()
        subcolumn = Gtk.TreeViewColumn("List of languages", subrenderer, text=0)
        self.sublistView.append_column(subcolumn)
        self.pathWin.hide()
        self.mainWin.show_all()
        Gtk.main()
    
    def windowQuit(self,widget):
        Gtk.main_quit
    
    def nextWindow(self,widget):
        logger.info("Next window")
        self.winNumber+=1
        self.showWindow()

    def showWindow(self):
        if self.winNumber == 1:
            self.mainWin.hide()
            self.pathWin.show_all()
        elif self.winNumber == 2:
            self.pathWin.hide()
            self.finalWin.show_all()

    
    def prevWindow(self,widget):
        logger.info("Prev window")
        self.mainWin.hide()
        self.pathWin.show_all()
    
    def cancelWindow(self,widget):
        logger.info("Cancel window")
    
    def storeRowActivated(self,widget,row,col):
        logger.info("handler for switch betwenn tools")
                
    def browsePath(self,window):
        logger.info("Browse path")
        dialog = Gtk.FileChooserDialog(
            "Please choose directory", self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
            )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.labelProjectName.set_text(dialog.get_filename())
        dialog.destroy()
        
    def runWizard(self,window):
        logger.info("Run wizard")
        name = self.labelProjectName.get_text()
        logger.info("Project name is: %s" % name)
        
