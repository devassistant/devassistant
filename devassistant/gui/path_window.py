# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import os
from gi.repository import Gtk
from devassistant.bin import CreatorAssistant

class PathWindow(object):
    def __init__(self, parent, main_window, builder, gui_helper):
        self.parent = parent
        self.main_window = main_window
        self.path_window = builder.get_object("pathWindow")
        self.dir_name = builder.get_object("dirName")
        self.entry_project_name = builder.get_object("entryProjectName")
        self.builder = builder
        self.gui_helper = gui_helper
        self.box_path_main = builder.get_object("boxPathMain")
        self.box_project = builder.get_object("boxProject")
        self.box6 = builder.get_object("box6")
        self.button = list()
        self.grid = self.gui_helper.create_gtk_grid(row_spacing=0,col_homogenous=False, row_homogenous=True)
        self.title = self.gui_helper.create_label("Available options:")
        self.title.set_alignment(0,0)
        self.entries = dict()
        self.browse_btns= dict()
        self.link_button = self.gui_helper.create_link_button(text="For registration visit GitHub Homepage", uri="https://www.github.com")
        self.link_button.connect("clicked", self.open_webbrowser)
        self.label_caption = self.builder.get_object("labelCaption")
        self.label_prj_name = self.builder.get_object("labelPrjName")
        self.label_prj_dir = self.builder.get_object("labelPrjDir")
        self.hseparator = self.builder.get_object("hseparator")

    def next_window(self, widget, data=None):
        #print self.parent.data
        if self.parent.data['AssistantType'] == 0:
            if self.dir_name.get_text() == "":
                md=self.gui_helper.create_message_dialog("Specify directory for project")
                md.run()
                md.destroy()
                return
            elif self.entry_project_name.get_text() == "":
                md=self.gui_helper.create_message_dialog("Specify project name")
                md.run()
                md.destroy()
                return
            else:
                # check whether directory is existing
                if os.path.isdir(self.dir_name.get_text()) == False:
                    md=self.gui_helper.create_message_dialog(
                        "Directory {0} does not exists".format(self.dir_name.get_text()))
                    md.run()
                    md.destroy()
                    return
                elif os.path.isdir(self.dir_name.get_text()+"/"+self.entry_project_name.get_text()) == True:
                    md=self.gui_helper.create_message_dialog(
                            "Directory {0} already exists".format(self.dir_name.get_text()+
                            "/"+self.entry_project_name.get_text()))
                    md.run()
                    md.destroy()
                    return
        for btn in filter(lambda x: x.get_active(), self.button):
            if btn.get_label() is None:
                continue
            if btn.get_label() in self.entries:
                for entry in filter(lambda x: x == btn.get_label(), self.entries):
                    if not self.entries[btn.get_label()].get_text():
                        md = self.gui_helper.create_message_dialog(
                            "Entry {0} is empty".format(btn.get_label())
                            )
                        md.run()
                        md.destroy()
                        return
                    self.parent.kwargs[btn.get_label().lower().replace('-','_')]=self.entries[btn.get_label()].get_text()
            else:
                self.parent.kwargs[btn.get_label().lower().replace('-','_')]=True
        if self.parent.data['AssistantType'] == 0:
            self.parent.kwargs['name']=self.dir_name.get_text()+"/"+self.entry_project_name.get_text()
        self.parent.run_window.open_window(widget, data)
        self.path_window.hide()

    def remove_widget_items(self):
        #self.box_path_main.remove(self.grid)
        #self.box_path_main.remove(self.title)
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
        self.dir_name.set_text(text)
        self.remove_widget_items()
        if self.parent.data['AssistantType'] != 0:
            self.box6.remove(self.box_project)
        else:
            self.box6.remove(self.box_path_main)
            self.box6.pack_start(self.box_project, False, False, 0)
            self.box6.pack_end(self.box_path_main, False, False, 0)
        self.box_path_main.pack_start(self.title, False, False, 0)
        caption_text = "Project: "
        row = 0
        # This cycle will show also options from parent assistant
        if isinstance(self.parent.assistant_class, CreatorAssistant):
            for arg in self.parent.assistant_class.args:
                row = self._add_table_row(arg, 0, row) +1
        for ass in filter(lambda x: x[0].name == self.parent.kwargs['subassistant_0'], self.parent.subass):
            caption_text+=" <b>"+ass[0].fullname+"</b>"
            if not ass[1]:
                for sub in filter(lambda x: not '--name' in x.flags, ass[0].args):
                    row = self._add_table_row(sub, len(sub.flags) - 1, row) + 1
            else:
                for sub in filter(lambda x: x[0].name == self.parent.kwargs['subassistant_1'], ass[1]):
                    caption_text+= " -> <b>"+ sub[0].fullname+"</b>"
                    for arg in filter(lambda x: not '--name' in x.flags, sub[0].args):
                        row = self._add_table_row(arg, len(arg.flags) - 1, row) + 1
        self.box_path_main.pack_start(self.grid, False, False, 0)
        self.label_caption.set_markup(caption_text)
        self.path_window.show_all()

    def _check_box_toggled(self, widget, data=None):
        active = widget.get_active()
        for entry in filter( lambda x: x == widget.get_label(), self.entries):
            if active:
                self.entries[widget.get_label()].set_sensitive(True)
                self.browse_btns[widget.get_label()].set_sensitive(True)
            else:
                self.entries[widget.get_label()].set_sensitive(False)
                self.browse_btns[widget.get_label()].set_sensitive(False)
        self.path_window.show_all()

    def prev_window(self, widget, data=None):
        self.path_window.hide()
        self.parent.open_window(widget, data)

    def get_data(self):
        return (self.dir_name.get_text(), self.entry_project_name.get_text())

    def browse_path(self, window):
        text = self.gui_helper.create_file_chooser_dialog("Choose project directory", self.path_window, name="Select")
        if text is not None:
            self.dir_name.set_text(text)

    def _check_box_title(self, arg, number):
        title = arg.flags[number][2:].title()
        return title

    def open_webbrowser(self, widget):
        import webbrowser
        webbrowser.open_new_tab(widget.get_uri())

    def _add_table_row(self, arg, number, row):
        act_btn = self.gui_helper.create_checkbox(self._check_box_title(arg, number))
        act_btn.set_alignment(0, 0)
        align = self.gui_helper.create_alignment()
        align.add(act_btn)
        self.button.append(act_btn)
        if row == 0:
            self.grid.add(align)
        else:
            self.grid.attach(align, 0, row , 1, 1)
        label = self.gui_helper.create_label(arg.kwargs['help'],justify=Gtk.Justification.LEFT)
        label.set_alignment(0, 0.1)
        self.grid.attach(label, 1, row, 1, 1)
        act_btn.connect("clicked", self._check_box_toggled)
        label_check_box = self.gui_helper.create_label(name="")
        self.grid.attach(label_check_box, 0, row, 1, 1)
        if arg.kwargs.get('action') != 'store_true':
            new_box = self.gui_helper.create_box(spacing=6)
            entry = self.gui_helper.create_entry(text="")
            align = self.gui_helper.create_alignment()
            align.add(entry)
            new_box.pack_start(align,False,False,6)
            align_btn = self.gui_helper.create_alignment()
            ''' If a button is needed please add there and in function
                _check_box_toggled
                Also do not forget to create a function for that button
                This can not be done by any automatic tool from those reasons
                Some fields needs a input user like user name for GitHub
                and some fields needs to have interaction from user like selecting directory
            '''
            self.browse_btn = self.gui_helper.button_with_label("Browse")
            self.browse_btn.connect("clicked", self.browse_clicked, entry)
            entry.set_text(arg.get_gui_hint('default'))
            if arg.kwargs.has_key('required'):
                self.browse_btn.set_sensitive(True)
                self.link_button.set_sensitive(True)
                entry.set_sensitive(True)
                act_btn.set_active(True)
                act_btn.set_sensitive(False)
            else:
                self.browse_btn.set_sensitive(False)
                self.link_button.set_sensitive(False)
                entry.set_sensitive(False)
                act_btn.set_active(False)
            if arg.get_gui_hint('type') == 'path':
                align_btn.add(self.browse_btn)
                self.browse_btns[self._check_box_title(arg,number)]=self.browse_btn
            elif arg.get_gui_hint('type') == 'str':
                if isinstance(self.parent.assistant_class,CreatorAssistant):
                    align_btn.add(self.link_button)
                    self.browse_btns[self._check_box_title(arg,number)]=self.link_button
            new_box.pack_start(align_btn, False, False, 6)
            row += 1
            self.entries[self._check_box_title(arg, number)] = entry
            self.grid.attach(new_box, 1, row, 1, 1)
        return row

    def browse_clicked(self, widget, data=None):
        text = self.gui_helper.create_file_chooser_dialog("Please select directory", self.path_window)
        if text is not None:
            data.set_text(text)
