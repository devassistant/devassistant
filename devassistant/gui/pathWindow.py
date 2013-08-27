# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import os
from devassistant.logger import logger
from devassistant.logger import logger_gui
from devassistant.gui import gui_helper
from gi.repository import Gtk

class pathWindow(object):
    def __init__(self, parent, mainWin, builder, gui_helper):
        self.parent = parent
        self.mainWin = mainWin
        self.pathWindow = builder.get_object("pathWindow")
        self.dirName = builder.get_object("dirName")
        self.entryProjectName = builder.get_object("entryProjectName")
        self.builder = builder
        self.gui_helper = gui_helper
        self.boxPathMain = builder.get_object("boxPathMain")
        self.boxProject = builder.get_object("boxProject")
        self.box6 = builder.get_object("box6")
        self.button = list()
        self.grid = self.gui_helper.create_gtk_grid(row_spacing=0,col_homogenous=False, row_homogenous=True)
        self.title = self.gui_helper.create_label("Available options:")
        self.title.set_alignment(0,0)
        self.entries = dict()
        self.browseBtns= dict()
        self.linkButton = self.gui_helper.create_link_button(text="For registration visit GitHub Homepage", uri="https://www.github.com")
        self.linkButton.connect("clicked", self.open_webbrowser)
        self.labelCaption = self.builder.get_object("labelCaption")
        self.labelPrjName = self.builder.get_object("labelPrjName")
        self.labelPrjDir = self.builder.get_object("labelPrjDir")
        self.hseparator = self.builder.get_object("hseparator")

    def next_window(self, widget, data=None):
        #print self.parent.data
        if self.parent.data['AssistantType'] == 0:
            if self.dirName.get_text() == "":
                md=self.gui_helper.create_message_dialog("Specify directory for project")
                md.run()
                md.destroy()
                return
            elif self.entryProjectName.get_text() == "":
                md=self.gui_helper.create_message_dialog("Specify project name")
                md.run()
                md.destroy()
                return
            else:
                # check whether directory is existing
                if os.path.isdir(self.dirName.get_text()) == False:
                    md=self.gui_helper.create_message_dialog(
                        "Directory {0} does not exists".format(self.dirName.get_text()))
                    md.run()
                    md.destroy()
                    return
                elif os.path.isdir(self.dirName.get_text()+"/"+self.entryProjectName.get_text()) == True:
                    md=self.gui_helper.create_message_dialog(
                            "Directory {0} already exists".format(self.dirName.get_text()+
                            "/"+self.entryProjectName.get_text()))
                    md.run()
                    md.destroy()
                    return
        for btn in filter(lambda x: x.get_active(), self.button):
            if btn.get_label() in self.entries:
                for entry in filter(lambda x: x == btn.get_label(), self.entries):
                    self.parent.kwargs[btn.get_label().lower().replace('-','_')]=self.entries[btn.get_label()].get_text()
            else:
                self.parent.kwargs[btn.get_label().lower().replace('-','_')]=None
        if self.parent.data['AssistantType'] == 0:
            self.parent.kwargs['name']=self.dirName.get_text()+"/"+self.entryProjectName.get_text()
        self.parent.runWindow.open_window(widget, data)
        self.pathWindow.hide()

    def remove_widget_items(self):
        #self.boxPathMain.remove(self.grid)
        #self.boxPathMain.remove(self.title)
        for btn in self.button:
            self.button.remove(btn)
        for btn in self.grid:
            self.grid.remove(btn)

    def get_user_path(self):
        try:
            path = os.path.expanduser('~')
        except Exception:
            path = ''
        if os.path.isdir(path):
            return path

    def open_window(self, widget, data=None):
        text = self.get_user_path()
        self.dirName.set_text(text)
        self.remove_widget_items()
        if self.parent.data['AssistantType'] != 0:
            self.box6.remove(self.boxProject)
        else:
            self.box6.remove(self.boxPathMain)
            self.box6.pack_start(self.boxProject, False, False, 0)
            self.box6.pack_end(self.boxPathMain, False, False, 0)
        self.boxPathMain.pack_start(self.title, False, False, 0)
        captionText = "Project: "
        row = 0
        for arg in self.parent.assistant_class.args:
            row = self._add_table_row(arg, 0, row) +1
        for ass in filter(lambda x: x[0].name == self.parent.kwargs['subassistant_0'], self.parent.subass):
            captionText+=" <b>"+ass[0].fullname+"</b>"
            if not ass[1]:
                for sub in filter(lambda x: x.flags[1] != '--name', ass[0].args):
                    row = self._add_table_row(sub, 1, row) + 1
            else:
                for sub in filter(lambda x: x[0].name == self.parent.kwargs['subassistant_1'], ass[1]):
                    captionText+= " -> <b>"+ sub[0].fullname+"</b>"
                    for arg in filter(lambda x: not '--name' in x.flags, sub[0].args):
                        row = self._add_table_row(arg, len(arg.flags) - 1, row) + 1
        self.boxPathMain.pack_start(self.grid, False, False, 0)
        self.labelCaption.set_markup(captionText)
        self.pathWindow.show_all()

    def _check_box_toggled(self, widget, data=None):
        active = widget.get_active()
        for entry in filter( lambda x: x == widget.get_label(), self.entries):
            if active:
                self.entries[widget.get_label()].set_sensitive(True)
                self.browseBtns[widget.get_label()].set_sensitive(True)
            else:
                self.entries[widget.get_label()].set_sensitive(False)
                self.browseBtns[widget.get_label()].set_sensitive(False)
        self.pathWindow.show_all()

    def prev_window(self, widget, data=None):
        self.pathWindow.hide()
        self.parent.open_window(widget, data)

    def get_data(self):
        return (self.dirName.get_text(), self.entryProjectName.get_text())

    def browse_path(self, window):
        text = self.gui_helper.create_file_chooser_dialog("Choose project directory", self.pathWindow, name="Select")
        if text is not None:
            self.dirName.set_text(text)

    def _check_box_title(self, arg, number):
        title = arg.flags[number][2:].title()
        return title

    def open_webbrowser(self, widget):
        import webbrowser
        webbrowser.open_new_tab(widget.get_uri())

    def _add_table_row(self, arg, number, row):
        actBtn = self.gui_helper.create_checkbox(self._check_box_title(arg, number))
        actBtn.set_alignment(0, 0)
        align = self.gui_helper.create_alignment()
        align.add(actBtn)
        self.button.append(actBtn)
        if row == 0:
            self.grid.add(align)
        else:
            self.grid.attach(align, 0, row , 1, 1)
        label = self.gui_helper.create_label(arg.kwargs['help'],justify=Gtk.Justification.LEFT)
        label.set_alignment(0, 0.1)
        self.grid.attach(label, 1, row, 1, 1)
        actBtn.connect("clicked", self._check_box_toggled)
        label_check_box = self.gui_helper.create_label(name="")
        self.grid.attach(label_check_box, 0, row, 1, 1)
        if arg.kwargs.get('action') != 'store_true':
            new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=6)
            new_box.set_homogeneous(False)
            entry = self.gui_helper.create_entry(text="")
            align = self.gui_helper.create_alignment()
            align.add(entry)
            new_box.pack_start(align,False,False,0)
            alignBtn = self.gui_helper.create_alignment()
            ''' If a button is needed please add there and in function
                _check_box_toggled
                Also do not forget to create a function for that button
                This can not be done by any automatic tool from those reasons
                Some fields needs a input user like user name for GitHub
                and some fields needs to have interaction from user like selecting directory
            '''
            self.browseBtn = self.gui_helper.button_with_label("Browse")
            self.browseBtn.set_sensitive(False)
            self.browseBtn.connect("clicked", self.browse_clicked, entry)
            entry.set_text(arg.get_gui_hint('default'))
            entry.set_sensitive(False)
            if arg.get_gui_hint('type') == 'path':
                alignBtn.add(self.browseBtn)
                self.browseBtns[self._check_box_title(arg,number)]=self.browseBtn
            elif arg.get_gui_hint('type') == 'str':
                alignBtn.add(self.linkButton)
                self.browseBtns[self._check_box_title(arg,number)]=self.linkButton
            new_box.pack_start(alignBtn, False, False, 0)
            row += 1
            self.entries[self._check_box_title(arg, number)] = entry
            self.grid.attach(new_box, 1, row, 1, 1)
        return row

    def browse_clicked(self, widget, data=None):
        text = self.gui_helper.create_file_chooser_dialog("Please select directory", self.pathWindow)
        if text is not None:
            data.set_text(text)
