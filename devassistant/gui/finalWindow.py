# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import mainWindow
import pathWindow
import os
import getpass

from devassistant.cli import argparse_generator
from devassistant.logger import logger
from devassistant.logger import logger_gui
from gi.repository import Gtk

class finalWindow(object):
    def __init__(self,  parent, pathWindow, builder):
        self.parent = parent
        self.pathWindow = pathWindow
        self.finalWindow = builder.get_object("finalWindow")
        self.runWindow = builder.get_object("runWindow")
        self.boxMain = builder.get_object("boxMain")
        self.button = []
        self.githubEntry = self._create_entry(text=getpass.getuser())
        self.eclipseEntry = self._create_entry(text=os.path.expanduser("~/workspace"))
        self.grid = Gtk.Grid()
        self.title = self._create_label("Available options:")

    def prev_window(self, widget, data=None):
        self.pathWindow.open_window(widget, data)
        self.finalWindow.hide()

    def _create_entry(self, text=""):
        textEntry = Gtk.Entry()
        textEntry.set_sensitive(False)
        textEntry.set_text(text)
        return textEntry

    def _create_label(self, text="None"):
        label = Gtk.Label(text)
        return label;

    def _add_table_row(self, arg, number, row):
        #print "Parser: %s" % arg
        #for flag in arg.flags:
        #    print "Flags: %s" % flag
        #for kwarg in arg.kwargs:
        #    print "Kwargs: %s" % type(kwarg)
        #print "nargs: %s " % arg.kwargs.get('nargs')
        #print "action: %s " % arg.kwargs.get('action')
        #print "help: %s " % arg.kwargs.get('help')
        actBtn = Gtk.CheckButton(arg.flags[number][2:].title())
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
        new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6)
        new_box.set_homogeneous(False)
        if arg.flags[number] == '--eclipse':
            new_box.pack_start(self.eclipseEntry,False,False,0)
            new_box.pack_start(self.browseBtn,False,False,0)
            row += 1
        elif arg.flags[number] == '--github':
            new_box.pack_start(self.githubEntry,False,False,0)
            row += 1
        self.grid.attach(label_check_box, 0, row, 1, 1)
        self.grid.attach(new_box, 1, row, 1, 1)
        return row

    def open_window(self, widget, data=None):
        logger_gui.info("open final window")
        selection = self.parent.listView.get_selection()
        subselection = self.parent.sublistView.get_selection()
        self.boxMain.remove(self.grid)
        self.boxMain.remove(self.title)
        for btn in self.button:
            self.button.remove(btn)
        for btn in self.grid:
            self.grid.remove(btn)
        self.browseBtn = Gtk.Button("Browse")
        self.browseBtn.connect("clicked", self.browse_clicked)
        self.browseBtn.set_sensitive(False)
        self.title.set_alignment(0,0)
        self.boxMain.pack_start(self.title, False, False, 12)
        self.grid.set_row_homogeneous(True)
        self.grid.set_column_spacing(12)
        self.grid.set_row_spacing(6)
        model, path_list = selection.get_selected()
        if path_list != None:
            submodel, subpath_list = subselection.get_selected()
            tool = model[path_list][0]
            for ass in filter(lambda x: x[0].fullname == tool, self.parent.subas):
                if not ass[1]:
                    row = 0
                    #parsed_args = argparse_generator.ArgparseGenerator.generate_argument_parser(ass)
                    for sub in filter(lambda x: x.flags[1] != '--name', ass[0].args):
                        row = self._add_table_row(sub, 1, row) + 1
                else:
                    for sub in filter(lambda x: x[0].fullname == submodel[subpath_list][0], ass[1]):
                        row = 0
                        for arg in filter(lambda x: not '--name' in x.flags, sub[0].args):
                            row = self._add_table_row(arg, len(arg.flags) - 1, row) + 1
        self.boxMain.pack_start(self.grid, False, False, 6)
        self.finalWindow.show_all()

    def _check_box_toggled(self, widget, data=None):
        active = widget.get_active()
        if widget.get_label() == "Github":
            if active:
                self.githubEntry.set_sensitive(True)
            else:
                self.githubEntry.set_sensitive(False)
        elif widget.get_label() == "Eclipse":
            if active:
                self.eclipseEntry.set_sensitive(True)
                self.browseBtn.set_sensitive(True)
            else:
                self.eclipseEntry.set_sensitive(False)
                self.browseBtn.set_sensitive(False)
        
    def run_btn(self, widget, data=None):
        logger_gui.info("run button")
        for btn in self.button:
            if btn.get_active():
                if btn.get_label() == "github":
                    self.parent.kwargs[btn.get_label().lower()]=self.githubEntry.get_text()
                elif btn.get_label() == "eclipse":
                    self.parent.kwargs[btn.get_label().lower()]=self.eclipseEntry.get_text()
                else:
                    self.parent.kwargs[btn.get_label().lower()]=None
            logger_gui.info("Name is:{0} {1}".format(btn.get_active(),btn.get_label().lower()))
        logger_gui.info(self.parent.kwargs)
        self.parent.runWindow.open_window(widget, data)
        self.finalWindow.hide()
        

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
