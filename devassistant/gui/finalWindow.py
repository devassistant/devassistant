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
#from devassistant.gui.logger_gui import logger_gui
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
        self.githubEntry.set_editable(0)
        self.githubEntry.set_text(getpass.getuser())
        self.eclipseEntry = Gtk.Entry()
        self.eclipseEntry.set_editable(0)
        self.eclipseEntry.set_text(os.path.expanduser("~/workspace"))
        self.browseBtn = Gtk.Button("Browse")
        self.browseBtn.connect("clicked", self.browse_clicked)

    def prev_window(self, widget, data=None):
        self.pathWindow.open_window(widget, data)
        self.finalWindow.hide()

    def open_window(self, widget, data=None):
        #logger_gui.info("open window")
        selection = self.parent.listView.get_selection()
        subselection = self.parent.sublistView.get_selection()
        title = Gtk.Label("List of all available options:")
        title.set_alignment(0,0)
        self.boxMain.pack_start(title, False, False, 12)
        boxFinal = Gtk.Box(spacing=12)
        boxFinal.set_homogeneous(False)
        model, path_list = selection.get_selected()
        submodel, subpath_list = subselection.get_selected()
        if path_list != None:
            tool = model[path_list][0]
            if tool in map(lambda x: x[0].fullname, self.parent.subas):
                for ass in self.parent.subas:
                    if tool == ass[0].fullname:
                        vbox_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6)
                        vbox_left.set_homogeneous(False)
                        vbox_right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6)
                        vbox_right.set_homogeneous(False)
                        boxFinal.pack_start(vbox_left, False, False, 0)
                        boxFinal.pack_end(vbox_right, False, False, 0)
                        if not ass[1]:
                            for sub in ass[0].args:
                                if sub.flags[1] != '--name':
                                    label = Gtk.Label()
                                    label.set_text(sub.kwargs['help'])
                                    label.set_alignment(0, 0)
                                    actBtn = Gtk.CheckButton(sub.flags[1][2:])
                                    vbox_left.pack_start(actBtn, False, False, 0)
                                    vbox_right.pack_start(label, False, False, 0)
                                    self.button.append(actBtn)
                                    if sub.flags[1] == '--eclipse':
                                        actBtn.connect("clicked", self.eclipse_toggled)
                                        labelEclipse = Gtk.Label()
                                        labelEclipse.set_text("")
                                        new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6)
                                        new_box.set_homogeneous(False)
                                        new_box.pack_start(self.eclipseEntry,False,False,0)
                                        new_box.pack_start(self.browseBtn,False,False,0)
                                        vbox_left.pack_start(labelEclipse,False,False,0)
                                        vbox_right.pack_start(new_box,False,False,0)
                                    elif sub.flags[1] == '--github':
                                        actBtn.connect("clicked", self.github_toggled)
                                        labelGitHub = Gtk.Label()
                                        labelGitHub.set_text("")
                                        new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6)
                                        new_box.set_homogeneous(False)
                                        new_box.pack_start(self.githubEntry,False,False,0)
                                        vbox_left.pack_start(labelGitHub,False,False,0)
                                        vbox_right.pack_start(new_box,False,False,0)
                        else:
                            #logger_gui.info("final_open_window {0}".format(submodel[subpath_list][0]))
                            for sub in ass[1]:
                                #logger_gui.info("ass[1] is: {0}".format(sub[0].fullname))
                                if submodel[subpath_list][0] == sub[0].fullname:
                                    for arg in sub[0].args:
                                        #logger_gui.info(arg)
                                        if arg.flags[1] != '--name':
                                            label = Gtk.Label()
                                            label.set_text(arg.kwargs['help'])
                                            label.set_alignment(0, 0)
                                            actBtn = Gtk.CheckButton(arg.flags[1][2:])
                                            vbox_left.pack_start(actBtn, True, True, 0)
                                            vbox_right.pack_start(label, True, True, 0)
                                            self.button.append(actBtn)
                                            if arg.flags[1] == '--eclipse':
                                                actBtn.connect("clicked", self.eclipse_toggled)
                                            elif arg.flags[1] == '--github':
                                                actBtn.connect("clicked", self.github_toggled)
        self.boxMain.pack_start(boxFinal, False, False, 6)
        self.finalWindow.show_all()
    def eclipse_toggled(self, widget, data=None):
        #logger_gui.debug("Eclipse_clicked")
        active = widget.get_active()
        #logger_gui.info(active)
        if active == True:
            self.eclipseEntry.set_editable(1)
        else:
            self.eclipseEntry.set_editable(0)
        
    def github_toggled(self, widget, data=None):
        #logger_gui.info("Github clicked")
        active = widget.get_active()
        #logger_gui.info(active)
        if active == True:
            self.githubEntry.set_editable(1)
        else:
            self.githubEntry.set_editable(0)

    def run_btn(self, widget, data=None):
        #logger_gui.info("run button")
        for btn in self.button:
            #logger_gui.info(btn)
            if btn.get_active() == True:
                self.parent.kwargs[btn.get_label()]=None
            #logger_gui.info("Name is:{0}{1}".format(btn.get_active(),btn.get_label()))
        #logger_gui.info(self.parent.kwargs)
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
