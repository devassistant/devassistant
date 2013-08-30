# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import os
import yaml
from devassistant.cli import argparse_generator
from devassistant.logger import logger
from devassistant.logger import logger_gui
from gi.repository import Gtk
from devassistant.bin import CreatorAssistant

class yamlWindow(object):
    def __init__(self, parent, mainWin, builder):
        self.parent = parent
        self.mainWin = mainWin
        self.yamlWindow = builder.get_object("yamlWindow")
        self.box6 = builder.get_object("box6")
        self.gui_helper = self.parent.gui_helper
        self.notebook = self.gui_helper.create_notebook()
        self.assistant_entry = None
        self.assistant_full = None
        self.assistant_desc = None
        self.list_view = None
        self.yaml_data = None
        self.full_assistant = None

        # general tab
        self._create_general()
        # Dependencies tab
        self._create_dependencies()
        # run tab
        self._create_run_section()
        self.box6.pack_start(self.notebook, True, True, 12)

    def _create_general(self):
        box_general = Gtk.Box(spacing=12,orientation=Gtk.Orientation.HORIZONTAL)
        scrolled_general = self.gui_helper.create_scrolled_window(box_general)
        scrolled_general.set_border_width(12)
        self.notebook.append_page(scrolled_general,
                                  Gtk.Label("General"))
        hbox1 = Gtk.Box(spacing=6,orientation=Gtk.Orientation.VERTICAL)
        hbox2 = Gtk.Box(spacing=6,orientation=Gtk.Orientation.VERTICAL)
        align1 = self.gui_helper.create_alignment()
        align2 = self.gui_helper.create_alignment()
        align3 = self.gui_helper.create_alignment()
        assistant_label = self.gui_helper.create_label("Assistant name:", wrap=False)
        assistant_fullname = self.gui_helper.create_label("Fullname:", wrap=False)
        assistant_description = self.gui_helper.create_label("Description:", wrap=False)
        align1.add(assistant_label)
        align2.add(assistant_fullname)
        align3.add(assistant_description)

        hbox1.pack_start(align1,False, False, 10)
        hbox1.pack_start(align2, False, False, 10)
        hbox1.pack_start(align3, False, False, 10)

        self.assistant_entry = self.gui_helper.create_entry(sensitive="True")
        self.assistant_full = self.gui_helper.create_entry(sensitive="True")
        self.assistant_desc = self.gui_helper.create_entry(sensitive="True")

        hbox2.pack_start(self.assistant_entry,False, False, 6)
        hbox2.pack_start(self.assistant_full, False, False, 6)
        hbox2.pack_start(self.assistant_desc, False, False, 6)

        box_general.pack_start(hbox1, False, False, 6)
        box_general.pack_start(hbox2, False, False, 6)

    def _create_dependencies(self):
        box_general = Gtk.Box(spacing=12,orientation=Gtk.Orientation.VERTICAL)
        box_general.set_homogeneous(False)
        box_general.set_border_width(12)
        self.notebook.append_page(box_general,
                                  Gtk.Label("Dependencies"))
        hbox1 = Gtk.Box(spacing=6,orientation=Gtk.Orientation.HORIZONTAL)
        hbox2 = Gtk.Box(spacing=6,orientation=Gtk.Orientation.HORIZONTAL)
        align1 = self.gui_helper.create_alignment()
        assistant_depend = self.gui_helper.create_label("Specify rpm dependencies:", wrap=False)
        align1.add(assistant_depend)

        hbox1.pack_start(align1,False, False, 10)

        self.list_store = Gtk.ListStore(str)
        self.list_view = self.gui_helper.create_tree_view(self.list_store)
        self.gui_helper.create_cell_renderer(self.list_view, title="rpm dependencies",assign=0)
        scrolled_dependecies = self.gui_helper.create_scrolled_window(self.list_view)
        scrolled_dependecies.set_border_width(12)

        hbox2.pack_start(scrolled_dependecies,True, True, 6)

        box_general.pack_start(hbox1, False, False, 6)
        box_general.pack_start(hbox2, True, True, 6)
        #box_general.pack_start(align1, False, False, 6)
        #box_general.pack_start(scrolled_dependecies, True, True, 6)

    def _create_run_section(self):
        box_run_section = Gtk.Box(spacing=12,orientation=Gtk.Orientation.VERTICAL)
        box_run_section.set_border_width(12)
        label_run = self.gui_helper.create_label("Specify run section")
        label_run.set_alignment(0,0)
        box_run_section.pack_start(label_run, False, False, 6)
        separator = Gtk.Separator()
        box_run_section.pack_start(separator, False, False, 6)
        self.text_view = self.gui_helper.create_textview()
        scrolled_run_section = self.gui_helper.create_scrolled_window(self.text_view)
        scrolled_run_section.set_border_width(12)
        box_run_section.pack_start(scrolled_run_section, True, True, 6)
        self.notebook.append_page(box_run_section,
                                  Gtk.Label("Run sections"))

    def _create_example_section(self):
        self.text_view = self.gui_helper.create_textview(editable=False)
        text_buffer = self.text_view.get_buffer()
        label = ""
        for ass in filter(lambda x: x[0].name == self.kwargs['subassistant_0'], self.parent.subas):
            if not ass[1]:
                ass[0].assert_fully_loaded()
                print ass[0]
                self.full_assistant = ass[0]
                text_buffer.set_text(self.get_yaml_data(ass[0].parsed_yaml))
                label = ass[0].fullname + " assistant"
                break
            if self.kwargs.has_key('subassistant_1'):
                for ass2 in filter(lambda x: x[0].name == self.kwargs['subassistant_1'], ass[1]):
                    ass2[0].assert_fully_loaded()
                    print ass2[0].parsed_yaml
                    self.full_assistant = ass2[0]
                    text_buffer.set_text(self.get_yaml_data(ass2[0].parsed_yaml))
                    label = ass2[0].fullname + " assistant"
        scrolled_example = self.gui_helper.create_scrolled_window(self.text_view)
        scrolled_example.set_border_width(12)
        self.notebook.append_page(scrolled_example,
                                  Gtk.Label(label))

    def get_yaml_data(self, yaml_data, style=False):
        self.yaml_data= yaml.dump(yaml_data, default_flow_style=style)
        return self.yaml_data

    def open_window(self, widget, data=None):
        self.kwargs = data
        if self.parent.kwargs['subassistant_0'] != "new_assistant":
            if self.notebook.get_n_pages() == 3:
                self._create_example_section()
                self.fill_data()
        else:
            self.notebook.remove_page(-1)
        self.yamlWindow.show_all()

    def prev_window(self, widget, data=None):
        self.yamlWindow.hide()
        self.parent.open_window(widget, data)

    def get_data(self):
        return (self.dirName.get_text(), self.entryProjectName.get_text())

    def fill_data(self):
        #rpm dependencies
        if self.full_assistant._dependencies[0].has_key('rpm'):
            map(lambda x: self.list_store.append([x]), self.full_assistant._dependencies[0].get('rpm'))
        else:
            for dep in self.full_assistant._dependencies:
                for d in dep.items():
                    self.list_store.append(d[1][0].get('rpm'))
        self.assistant_desc.set_text(self.full_assistant.description)
        self.assistant_full.set_text(self.full_assistant.fullname)

    def run_btn(self, widget, data=None):
        yaml_dict=dict()
        texts=dict()
        texts['description']=self.assistant_full.get_text()
        texts['fullname']=self.assistant_desc.get_text()
        yaml_dict[self.assistant_entry.get_text()]=texts
        #yaml_dict['fullname']=self.assistant_full.get_text()
        #yaml_dict['description']=self.assistant_desc.get_text()
        with open("mytest.yaml","w") as file:
            file.write(yaml.dump(yaml_dict, default_flow_style=False))
