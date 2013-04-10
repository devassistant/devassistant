# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import mainWindow
import pathWindow
from devassistant.logger import logging
from gi.repository import Gtk

class finalWindow(object):
    def __init__(self,  parent, pathWindow, builder):
        self.parent = parent
        self.pathWindow = pathWindow
        self.finalWindow = builder.get_object("finalWindow")
        self.runWindow = builder.get_object("runWindow")
        self.boxMain = builder.get_object("boxMain")
        self.button = []

    def prev_window(self, widget, data=None):
        self.pathWindow.open_window(widget, data)
        self.finalWindow.hide()

    def open_window(self, widget, data=None):
        logging.info("open window")
        selection = self.parent.listView.get_selection()
        subselection = self.parent.sublistView.get_selection()
        title = Gtk.Label("List of all available options:")
        title.set_alignment(0,0)
        self.boxMain.pack_start(title, False, False, 0)
        boxFinal = Gtk.Box(spacing=6)
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
                        boxFinal.pack_start(vbox_left, True, True, 0)
                        boxFinal.pack_start(vbox_right, True, True, 0)
                        if not ass[1]:
                            for sub in ass[0].args:
                                if sub.flags[1] != '--name':
                                    label = Gtk.Label()
                                    label.set_text(sub.kwargs['help'])
                                    label.set_alignment(0, 0)
                                    actBtn = Gtk.CheckButton(sub.flags[1][2:])
                                    vbox_left.pack_start(actBtn, True, True, 0)
                                    vbox_right.pack_start(label, True, True, 0)
                                    self.button.append(actBtn)
                                    if sub.flags[1] == '--eclipse':
                                        actBtn.connect("clicked", self.eclipse_toggled)
                                    elif sub.flags[1] == '--github':
                                        actBtn.connect("clicked", self.github_toggled)
                        else:
                            logging.info("final_open_window {0}".format(submodel[subpath_list][0]))
                            for sub in ass[1]:
                                logging.info("ass[1] is: {0}".format(sub[0].fullname))
                                if submodel[subpath_list][0] == sub[0].fullname:
                                    for arg in sub[0].args:
                                        logging.info(arg)
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
        logging.info("Eclipse_clicked")
        active = widget.get_active()
        logging.info(active)
        
    def github_toggled(self, widget, data=None):
        logging.info("Github clicked")
        active = widget.get_active()
        logging.info(active)

    def run_btn(self, widget, data=None):
        logging.info("run button")
        for btn in self.button:
            #logging.info(btn)
            logging.info("Name is:{0}{1}".format(btn.get_active(),btn.get_label()))
        self.parent.runWindow.open_window(widget, data)
        self.finalWindow.hide()
        
