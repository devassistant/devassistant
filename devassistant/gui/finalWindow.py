# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import mainWindow
import pathWindow
import os
import getpass

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
        self.githubEntry = Gtk.Entry()
        self.githubEntry.set_sensitive(False)
        self.githubEntry.set_text(getpass.getuser())
        self.eclipseEntry = Gtk.Entry()
        self.eclipseEntry.set_sensitive(False)
        self.eclipseEntry.set_text(os.path.expanduser("~/workspace"))
        self.grid = Gtk.Grid()
        self.title = Gtk.Label("Available options:")

    def prev_window(self, widget, data=None):
        self.pathWindow.open_window(widget, data)
        self.finalWindow.hide()

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
        submodel, subpath_list = subselection.get_selected()
        if path_list != None:
            tool = model[path_list][0]
            if tool in map(lambda x: x[0].fullname, self.parent.subas):
                for ass in self.parent.subas:
                    if tool == ass[0].fullname:
                        if not ass[1]:
                            row = 0
                            for sub in ass[0].args:
                                if sub.flags[1] != '--name':
                                    label = Gtk.Label()
                                    label.set_text(sub.kwargs['help'])
                                    label.set_alignment(0, 0)
                                    label.set_line_wrap(True)
                                    actBtn = Gtk.CheckButton(sub.flags[1][2:])
                                    align = Gtk.Alignment(xalign=0, yalign=0, xscale=0, yscale=0)
                                    self.button.append(actBtn)
                                    align.add(actBtn)
                                    if row == 0:
                                        self.grid.add(align)
                                    else:
                                        self.grid.attach(align, 0, row , 1, 1)
                                    self.grid.attach(label, 1, row, 1, 1) 
                                    if sub.flags[1] == '--eclipse':
                                        actBtn.connect("clicked", self.eclipse_toggled)
                                        labelEclipse = Gtk.Label()
                                        labelEclipse.set_text("")
                                        new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6)
                                        new_box.set_homogeneous(False)
                                        new_box.pack_start(self.eclipseEntry,False,False,0)
                                        new_box.pack_start(self.browseBtn,False,False,0)
                                        row += 1
                                        self.grid.attach(labelEclipse , 0, row, 1, 1)
                                        self.grid.attach(new_box, 1, row, 1, 1)
                                    elif sub.flags[1] == '--github':
                                        actBtn.connect("clicked", self.github_toggled)
                                        labelGitHub = Gtk.Label()
                                        labelGitHub.set_text("")
                                        new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6)
                                        new_box.set_homogeneous(False)
                                        new_box.pack_start(self.githubEntry,False,False,0)
                                        row += 1
                                        self.grid.attach(labelGitHub , 0, row, 1, 1)
                                        self.grid.attach(new_box, 1, row, 1, 1)
                                    row += 1
                        else:
                            logger_gui.info("final_open_window {0}".format(submodel[subpath_list][0]))
                            for sub in ass[1]:
                                logger_gui.info("ass[1] is: {0}".format(sub[0].fullname))
                                if submodel[subpath_list][0] == sub[0].fullname:
                                    row = 0
                                    for arg in sub[0].args:
                                        number = len(arg.flags) - 1
                                        if arg.flags[number] != '--name':
                                            label = Gtk.Label()
                                            label.set_text(arg.kwargs['help'])
                                            label.set_alignment(0, 0)
                                            label.set_line_wrap(True)
                                            actBtn = Gtk.CheckButton(arg.flags[number][2:])
                                            align = Gtk.Alignment(xalign=0, yalign=0, xscale=0, yscale=0)
                                            self.button.append(actBtn)
                                            align.add(actBtn)
                                            if row == 0:
                                                self.grid.add(align)
                                            else:
                                                self.grid.attach(align, 0, row , 1, 1)
                                            self.grid.attach(label, 1, row, 1, 1) 
                                            if arg.flags[number] == '--eclipse':
                                                actBtn.connect("clicked", self.eclipse_toggled)
                                                labelEclipse = Gtk.Label()
                                                labelEclipse.set_text("")
                                                new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6)
                                                new_box.set_homogeneous(False)
                                                new_box.pack_start(self.eclipseEntry,False,False,0)
                                                new_box.pack_start(self.browseBtn,False,False,0)
                                                row += 1
                                                self.grid.attach(labelEclipse , 0, row, 1, 1)
                                                self.grid.attach(new_box, 1, row, 1, 1)
                                            elif arg.flags[number] == '--github':
                                                actBtn.connect("clicked", self.github_toggled)
                                                labelGitHub = Gtk.Label()
                                                labelGitHub.set_text("")
                                                new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6)
                                                new_box.set_homogeneous(False)
                                                new_box.pack_start(self.githubEntry,False,False,0)
                                                row += 1
                                                self.grid.attach(labelGitHub , 0, row, 1, 1)
                                                self.grid.attach(new_box, 1, row, 1, 1)
                                            row += 1
        self.boxMain.pack_start(self.grid, False, False, 6)
        self.finalWindow.show_all()
    def eclipse_toggled(self, widget, data=None):
        active = widget.get_active()
        if active == True:
            self.eclipseEntry.set_sensitive(True)
            self.browseBtn.set_sensitive(True)
        else:
            self.eclipseEntry.set_sensitive(False)
            self.browseBtn.set_sensitive(False)
        
    def github_toggled(self, widget, data=None):
        active = widget.get_active()
        if active == True:
            self.githubEntry.set_sensitive(True)
        else:
            self.githubEntry.set_sensitive(False)

    def run_btn(self, widget, data=None):
        logger_gui.info("run button")
        for btn in self.button:
            if btn.get_active() == True:
                self.parent.kwargs[btn.get_label()]=None
            logger_gui.info("Name is:{0}{1}".format(btn.get_active(),btn.get_label()))
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
