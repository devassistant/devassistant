# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import os
import getpass
import mainWindow
import runWindow
from devassistant.cli import argparse_generator
from devassistant.logger import logger
from devassistant.logger import logger_gui
from gi.repository import Gtk

class pathWindow(object):
    def __init__(self, parent, mainWin, builder):
        self.parent = parent
        self.mainWin = mainWin
        self.pathWindow = builder.get_object("pathWindow")
        self.dirName = builder.get_object("dirName")
        self.entryProjectName = builder.get_object("entryProjectName")
        self.builder = builder
        self.boxPathMain = builder.get_object("boxPathMain")
        self.button = []
        self.grid = Gtk.Grid()
        self.title = self._create_label("Available options:")
        self.browseBtn = Gtk.Button("Browse")
        self.browseBtn.connect("clicked", self.browse_clicked)
        self.browseBtn.set_sensitive(False)
        self.entries = {}
        self.linkButton = self._create_link_button(text="For registration visit GitHub Homepage", uri="https://www.github.com")
        self.linkButton.connect("clicked", self.open_webbrowser)
        self.labelCaption = self.builder.get_object("labelCaption")
        
    def next_window(self, widget, data=None):
        if self.dirName.get_text() == "":
            md=Gtk.MessageDialog(None,
                                 Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                 Gtk.MessageType.WARNING,
                                 Gtk.ButtonsType.CLOSE,
                                 "Specify directory for project")
            md.run()
            md.destroy()
        elif self.entryProjectName.get_text() == "":
            md=Gtk.MessageDialog(None,
                                 Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                 Gtk.MessageType.WARNING,
                                 Gtk.ButtonsType.CLOSE,
                                 "Specify project name")
            md.run()
            md.destroy()
        else:
            # check whether directory is existing
            if os.path.isdir(self.dirName.get_text()) == False:
                md=Gtk.MessageDialog(None,
                                     Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                     Gtk.MessageType.WARNING,
                                     Gtk.ButtonsType.CLOSE,
                                     "Directory {0} does not exists".format(self.dirName.get_text()))
                md.run()
                md.destroy()
            elif os.path.isdir(self.dirName.get_text()+"/"+self.entryProjectName.get_text()) == True:
                md=Gtk.MessageDialog(None,
                                     Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                     Gtk.MessageType.WARNING,
                                     Gtk.ButtonsType.CLOSE,
                                     "Directory {0} already exists".format(self.dirName.get_text()+"/"+self.entryProjectName.get_text()))
                md.run()
                md.destroy()
            else:
                self.parent.kwargs['name']=self.dirName.get_text()+"/"+self.entryProjectName.get_text()
                self.parent.finalWindow.open_window(widget, data)
                self.pathWindow.hide()
        
    def open_window(self, widget, data=None):
        try:
            path = os.path.expanduser('~')
        except Exception:
            path = ''
        if os.path.isdir(path):
            self.dirName.set_text(path)
        #logger_gui.info("Prev window")
        self.boxPathMain.remove(self.grid)
        self.boxPathMain.remove(self.title)
        for btn in self.button:
            self.button.remove(btn)
        for btn in self.grid:
            self.grid.remove(btn)
        self.title.set_alignment(0,0)
        self.boxPathMain.pack_start(self.title, False, False, 12)
        self.grid.set_row_homogeneous(True)
        self.grid.set_column_spacing(12)
        self.grid.set_row_spacing(6)
        captionText = "Project: "
        for ass in filter(lambda x: x[0].name == self.parent.kwargs['subassistant_0'], self.parent.subas):
            captionText+=" <b>"+ass[0].fullname+"</b>"
            if not ass[1]:
                row = 0
                for sub in filter(lambda x: x.flags[1] != '--name', ass[0].args):
                    row = self._add_table_row(sub, 1, row) + 1
            else:
                for sub in filter(lambda x: x[0].name == self.parent.kwargs['subassistant_1'], ass[1]):
                    row = 0
                    captionText+= " subassistant: <b>"+ sub[0].fullname+"</b>"
                    for arg in filter(lambda x: not '--name' in x.flags, sub[0].args):
                        row = self._add_table_row(arg, len(arg.flags) - 1, row) + 1
        self.boxPathMain.pack_start(self.grid, False, False, 12)
        self.labelCaption.set_markup(captionText)
        self.pathWindow.show_all()

    def _check_box_toggled(self, widget, data=None):
        active = widget.get_active()
        for entry in filter( lambda x: x == widget.get_label(), self.entries):
            if active:
                self.entries[widget.get_label()].set_sensitive(True)
            else:
                self.entries[widget.get_label()].set_sensitive(False)
            if widget.get_label() == "Eclipse":
                if active:
                    self.browseBtn.set_sensitive(True)
                else:
                    self.browseBtn.set_sensitive(False)
        self.pathWindow.show_all()
   
    def prev_window(self, widget, data=None):
        self.pathWindow.hide()
        self.parent.open_window(widget, data)
    
    def get_data(self):
        return (self.dirName.get_text(), self.entryProjectName.get_text())
        
    def browse_path(self, window):
        dialog = Gtk.FileChooserDialog(
            "Choose project directory", self.pathWindow,
            Gtk.FileChooserAction.CREATE_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             "Select", Gtk.ResponseType.OK)
            )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.dirName.set_text(dialog.get_filename())
        dialog.destroy()
        
    def _create_entry(self, text=""):
        textEntry = Gtk.Entry()
        textEntry.set_sensitive(False)
        textEntry.set_text(text)
        return textEntry

    def _create_label(self, text="None"):
        label = Gtk.Label(text)
        return label;
    
    def _create_link_button(self, text="None", uri="None"):
        linkbtn = Gtk.LinkButton(uri, text)
        return linkbtn;
    
    def _check_box_title(self, arg, number):
        title = arg.flags[number][2:].title()
        return title

    def open_webbrowser(self, widget):
        import webbrowser
        webbrowser.open_new_tab(widget.get_uri())

    def _add_table_row(self, arg, number, row):
        actBtn = Gtk.CheckButton(self._check_box_title(arg, number))
        align = Gtk.Alignment(xalign=0, yalign=0, xscale=0, yscale=0)
        self.button.append(actBtn)
        align.add(actBtn)
        if row == 0:
            self.grid.add(align)
        else:
            self.grid.attach(align, 0, row , 1, 1)
        label = self._create_label(arg.kwargs['help'])
        label.set_alignment(0, 0)
        label.set_line_wrap(True)
        self.grid.attach(label, 1, row, 1, 1) 
        actBtn.connect("clicked", self._check_box_toggled)
        label_check_box = self._create_label(text="")
        self.grid.attach(label_check_box, 0, row, 1, 1)
        if arg.kwargs.get('action') != 'store_true':
            new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6)
            new_box.set_homogeneous(False)
            entry = self._create_entry(text="")
            new_box.pack_start(entry,False,False,0)
            ''' If a button is needed please add there and in function
                _check_box_toggled
                Also do not forget to create a function for that button
                This can not be done by any automatic tool from those reasons
                Some fields needs a input user like user name for GitHub
                and some fields needs to have interaction from user like selecting directory
            '''
            if self._check_box_title(arg, number) == 'Eclipse':
                entry.set_text(text=os.path.expanduser("~/workspace"))
                new_box.pack_start(self.browseBtn,False,False,0)
            elif self._check_box_title(arg, number) == 'Github':
                entry.set_text(text=getpass.getuser())
                new_box.pack_start(self.linkButton,False,False,0)
            row += 1
            self.entries[self._check_box_title(arg, number)] = entry
            self.grid.attach(new_box, 1, row, 1, 1) 
        return row

    def run_btn(self, widget, data=None):
        #logger_gui.info("run button")
        for btn in filter(lambda x: x.get_active(), self.button):
            if btn.get_label() in self.entries:
                for entry in filter(lambda x: x == btn.get_label(), self.entries):
                    self.parent.kwargs[btn.get_label().lower()]=self.entries[btn.get_label()].get_text()
            else:
                self.parent.kwargs[btn.get_label().lower()]=None
            #logger_gui.info("Name is:{0} {1}".format(btn.get_active(),btn.get_label().lower()))
        #logger_gui.info(self.parent.kwargs)
        self.parent.runWindow.open_window(widget, data)
        self.pathWindow.hide()
        
    def browse_clicked(self, widget, data=None):
        dialog = Gtk.FileChooserDialog(
            "Please Eclipse workspace directory", self.finalWindow,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
            )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.eclipseEntry.set_text(dialog.get_filename())
        dialog.destroy()
