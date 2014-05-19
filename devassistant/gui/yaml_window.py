# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import yaml
from gi.repository import Gtk

class YamlWindow(object):
    def __init__(self, parent, main_win, builder):
        self.parent = parent
        self.main_win = main_win
        self.yaml_window = builder.get_object("yamlWindow")
        self.box6 = builder.get_object("box6")
        self.gui_helper = self.parent.gui_helper
        self.notebook = self.gui_helper.create_notebook()
        self.assistant_entry = None
        self.assistant_full = None
        self.assistant_desc = None
        self.list_view = None
        self.yaml_data = None
        self.full_assistant = None
        self.run_view = None
        self.list_selection = None

        # general tab
        self._create_general()
        # Dependencies tab
        self._create_dependencies()
        # run tab
        self._create_run_section()
        self.box6.pack_start(self.notebook, True, True, 12)

    def _create_general(self):
        box_general = self.gui_helper.create_box(spacing=12)
        scrolled_general = self.gui_helper.create_scrolled_window(box_general)
        scrolled_general.set_border_width(12)
        self.notebook.append_page(scrolled_general,
                                  Gtk.Label("General"))
        hbox1 = self.gui_helper.create_box(spacing=6,orientation=Gtk.Orientation.VERTICAL)
        hbox2 = self.gui_helper.create_box(spacing=6,orientation=Gtk.Orientation.VERTICAL)
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
        box_general = self.gui_helper.create_box(spacing=12,orientation=Gtk.Orientation.VERTICAL)
        box_general.set_border_width(12)
        self.notebook.append_page(box_general,
                                  Gtk.Label("Dependencies"))
        hbox1 = self.gui_helper.create_box(spacing=6)
        hbox2 = self.gui_helper.create_box(spacing=6)
        align1 = self.gui_helper.create_alignment()
        assistant_depend = self.gui_helper.create_label("Specify package dependencies:", wrap=False)
        align1.add(assistant_depend)

        hbox1.pack_start(align1,False, False, 10)

        self.list_store = Gtk.ListStore(str, str)
        pkg_manager = Gtk.ListStore(str)
        pkg_manager.append(["rpm"])
        pkg_manager.append(["pip"])
        pkg_manager.append(["npm"])
        self.list_view = self.gui_helper.create_tree_view(self.list_store)
        self.gui_helper.create_cell_renderer_combo(self.list_view, title="Package manager",assign=0, editable=True, model=pkg_manager, function=self._select_pkg_manager)
        self.gui_helper.create_cell_renderer_text(self.list_view, title="Package dependencies",assign=1, editable=True)
        self.list_selection = self.list_view.get_selection()
        self.list_selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.list_selection.connect("changed", self._list_changed)
        scrolled_dependecies = self.gui_helper.create_scrolled_window(self.list_view)
        scrolled_dependecies.set_border_width(12)

        hbox3 = self.gui_helper.create_box(spacing=6,orientation=Gtk.Orientation.VERTICAL)
        btn_add = self.gui_helper.button_with_label("Add")
        btn_add.connect("clicked", self._add_dependency_row)
        btn_remove = self.gui_helper.button_with_label("Remove")
        btn_remove.connect("clicked", self._delete_dependency_row)
        hbox2.pack_start(scrolled_dependecies,True, True, 6)
        hbox3.pack_start(btn_add, False, True, 6)
        hbox3.pack_start(btn_remove, False, True, 6)
        hbox2.pack_start(hbox3,False, False, 6)

        box_general.pack_start(hbox1, False, False, 6)
        box_general.pack_start(hbox2, True, True, 6)

        #box_general.pack_start(align1, False, False, 6)
        #box_general.pack_start(scrolled_dependecies, True, True, 6)

    def _create_run_section(self):
        box_run_section = self.gui_helper.create_box(spacing=12,orientation=Gtk.Orientation.VERTICAL)
        box_run_section.set_border_width(12)
        label_run = self.gui_helper.create_label("Specify run section. Each row is one row in YAML file and begin with dash (-). ")
        label_run.set_alignment(0,0)
        box_run_section.pack_start(label_run, False, False, 6)
        separator = Gtk.Separator()
        box_run_section.pack_start(separator, False, False, 6)
        self.run_view = self.gui_helper.create_textview()
        scrolled_run_section = self.gui_helper.create_scrolled_window(self.run_view)
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
                self.full_assistant = ass[0]
                text_buffer.set_text(self._get_yaml_data(ass[0].parsed_yaml))
                label = ass[0].fullname + " assistant"
                break
            if 'subassistant_1' in self.kwargs:
                for ass2 in filter(lambda x: x[0].name == self.kwargs['subassistant_1'], ass[1]):
                    ass2[0].assert_fully_loaded()
                    self.full_assistant = ass2[0]
                    text_buffer.set_text(self._get_yaml_data(ass2[0].parsed_yaml))
                    label = ass2[0].fullname + " assistant"
        scrolled_example = self.gui_helper.create_scrolled_window(self.text_view)
        scrolled_example.set_border_width(12)
        self.notebook.append_page(scrolled_example,
                                  Gtk.Label(label))

    def _get_yaml_data(self, yaml_data, style=False):
        self.yaml_data= yaml.dump(yaml_data, default_flow_style=style)
        return self.yaml_data

    def open_window(self, widget, data=None):
        self.kwargs = data
        if self.parent.kwargs['subassistant_0'] != "new_assistant":
            if self.notebook.get_n_pages() == 3:
                self._create_example_section()
                self._fill_data()
        else:
            self.notebook.remove_page(-1)
        self.yaml_window.show_all()

    def prev_window(self, widget, data=None):
        self.yaml_window.hide()
        self.parent.open_window(widget, data)

    def _get_data(self):
        return (self.dir_name.get_text(), self.entry_project_name.get_text())

    def _fill_data(self):
        #rpm dependencies
        if 'rpm' in self.full_assistant._dependencies[0]:
            #for d in self.full_assistant._dependencies[0].get('rpm'):
            #    self.list_store.append(['rpm', d])
            map(lambda x: self.list_store.append(['rpm',x]), self.full_assistant._dependencies[0].get('rpm'))
        else:
            for depend in self.full_assistant._dependencies:
                if 'rpm' in depend:
                    map(lambda x: self.list_store.append(['rpm', x]),depend.items())
                else:
                    for dep in depend.items():
                        for d in dep:
                            if not isinstance(d,basestring):
                                if 'rpm' in d[0]:
                                    map(lambda x: self.list_store.append(['rpm', x]), d[0].get('rpm'))
        self.assistant_desc.set_text(self.full_assistant.description)
        self.assistant_full.set_text(self.full_assistant.fullname)

    def run_btn(self, widget, data=None):
        yaml_dict=dict()
        texts=dict()
        texts['description']=self.assistant_full.get_text()
        texts['fullname']=self.assistant_desc.get_text()
        if not self.assistant_entry.get_text():
            dlg = self.gui_helper.create_message_dialog("You have to write assistant name")
            dlg.run()
            dlg.destroy()
            return
        buf = self.run_view.get_buffer()
        start = buf.get_start_iter()
        end = buf.get_end_iter()
        run_list = buf.get_text(start, end, False).split('\n')
        texts['run']=run_list
        yaml_dict[self.assistant_entry.get_text()]=texts
        with open("mytest.yaml","w") as file:
            file.write(yaml.dump(yaml_dict, default_flow_style=False))

    def _add_dependency_row(self, widget, data=None):
        self.list_store.append()

    def _delete_dependency_row(self, widget, data=None):
        print("Delete row")

    def _select_pkg_manager(self,widget,path,text):
        self.list_store[path][0] = text

    def _list_changed(self, selection):
        print("list change")
        model, listiter = selection.get_selected()
        if listiter != None:
            print("Selected", model[listiter][1])
