# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import os
from gi.repository import Gtk


class PathWindow(object):
    """
    Class shows option dialogs and checks settings for each
    assistant
    """
    def __init__(self, parent, main_window, builder, gui_helper):
        self.parent = parent
        self.main_window = main_window
        self.path_window = builder.get_object("pathWindow")
        self.dir_name = builder.get_object("dirName")
        self.dir_name_browse_btn = builder.get_object("browsePathBtn")
        self.entry_project_name = builder.get_object("entryProjectName")
        self.builder = builder
        self.gui_helper = gui_helper
        self.box_path_main = builder.get_object("boxPathMain")
        self.box_project = builder.get_object("boxProject")
        self.box6 = builder.get_object("box6")
        self.run_btn = builder.get_object("nextPathBtn")
        self.button = dict()
        self.grid = self.gui_helper.create_gtk_grid(row_spacing=0,
                                                    col_homogenous=False,
                                                    row_homogenous=False)
        self.title = self.gui_helper.create_label("Available options:")
        self.title.set_alignment(0, 0)
        self.box_path_main.pack_start(self.title, False, False, 0)
        self.box_path_main.pack_start(self.grid, False, False, 0)
        self.entries = dict()
        self.browse_btns = dict()
        self.kwargs = dict()
        self.label_caption = self.builder.get_object("labelCaption")
        self.label_prj_name = self.builder.get_object("labelPrjName")
        self.label_prj_dir = self.builder.get_object("labelPrjDir")
        self.label_full_prj_dir = self.builder.get_object("labelFullPrjDir")
        self.h_separator = self.builder.get_object("hseparator")
        self.back_button = False
        self.top_assistant = None
        self.project_name_shown = True
        self.current_main_assistant = None
        self.data = dict()
        self.browse_btn = None
        self.link_button = None

    def check_for_directory(self, dirname):
        """
        Function checks the directory and report it to user
        """
        return self.gui_helper.execute_dialog(
            "Directory {0} already exists".format(
            dirname))

    def get_full_dir_name(self):
        """
        Function returns a full dir name
        """
        return os.path.join(self.dir_name.get_text(), self.entry_project_name.get_text())

    def next_window(self, widget, data=None):
        """
        Function opens the run Window who executes the
        assistant project creation
        """
        # check whether deps-only is selected
        deps_only = False
        for active in [x for x in self.button if isinstance(x, Gtk.CheckButton) and x.get_active()]:
            if self.gui_helper.get_btn_lower_label(active) == "deps-only":
                deps_only = True
        project_dir = self.dir_name.get_text()
        full_name = self.get_full_dir_name()

        # check whether project directory and name is properly set
        if not deps_only and self.current_main_assistant.name == 'crt':
            if project_dir == "":
                return self.gui_helper.execute_dialog("Specify directory for project")
            else:
                # check whether directory is existing
                if not os.path.isdir(project_dir):
                    response = self.gui_helper.create_question_dialog(
                        "Directory {0} does not exists".format(project_dir),
                        "Do you want to create them?"
                    )
                    if response == Gtk.ResponseType.NO:
                        # User do not want to create a directory
                        return
                    else:
                        # Create directory
                        try:
                            os.makedirs(project_dir)
                        except OSError as os_err:
                            return self.gui_helper.execute_dialog("{0}".format(os_err))
                elif os.path.isdir(full_name):
                    return self.check_for_directory(full_name)

        if not self._build_flags():
            return

        if not deps_only and self.current_main_assistant.name == 'crt':
            self.kwargs['name'] = full_name

        self.data['kwargs'] = self.kwargs
        self.data['top_assistant'] = self.top_assistant
        self.data['current_main_assistant'] = self.current_main_assistant
        self.parent.run_window.open_window(widget, self.data)
        self.path_window.hide()

    def _build_flags(self):
        """
        Function builds kwargs variable for run_window
        """
        for widget in self.button:
            if isinstance(widget, Gtk.Label) or isinstance(widget, Gtk.CheckButton) and widget.get_active():
                if widget.get_label() in self.entries and not self.entries[widget.get_label()].get_text():
                    self.gui_helper.execute_dialog(
                        "Entry {0} is empty".format(widget.get_label())
                    )
                    return False
        for label in [x for x in self.button if isinstance(x, Gtk.Label)]:
            self.kwargs[label.get_label().lower()] = self.entries[label.get_label()].get_text()

        check_button = [x for x in self.button if isinstance(x, Gtk.CheckButton)]
        # Check for active CheckButtons
        for active in [x for x in check_button if x.get_active()]:
            lbl = self.gui_helper.get_btn_lower_replace(active)
            btn = self.gui_helper.get_btn_label(active)
            if not btn in self.entries:
                if self.button[active].get_gui_hint('type') == 'const':
                    self.kwargs[lbl] = self.button[active].kwargs['const']
                else:
                    self.kwargs[lbl] = True
                continue
            for entry in [x for x in self.entries if x == btn]:
                self.kwargs[lbl] = self.entries[btn].get_text()

        # Check for non active CheckButtons but with defaults flag
        for not_active in [x for x in check_button if not x.get_active()]:
            lbl = self.gui_helper.get_btn_lower_replace(not_active)
            if 'default' in self.button[not_active].kwargs:
                self.kwargs[lbl] = self.button[not_active].get_gui_hint('default')
            elif self.back_button and lbl in self.kwargs:
                del self.kwargs[lbl]
        return True

    def _remove_widget_items(self):
        """
        Function removes widgets from grid
        """
        self.button = dict()
        for btn in self.grid:
            self.grid.remove(btn)

    def get_user_path(self):
        """
        Function returns a path either user home directory
        or empty directory
        """
        try:
            path = os.path.expanduser('~')
        except Exception:
            path = ''
        if os.path.isdir(path):
            return path

    def open_window(self, widget, data=None):
        """
        Function opens the Options dialog
        """
        if data is not None:
            self.back_button = data.get('back', False)
            self.top_assistant = data.get('top_assistant', None)
            self.current_main_assistant = data.get('current_main_assistant', None)
            self.kwargs = data.get('kwargs', None)
            self.data['debugging'] = data.get('debugging', False)
        text = self.get_user_path()
        self.dir_name.set_text(text)
        self.label_full_prj_dir.set_text(text)
        self.dir_name.set_sensitive(True)
        self.dir_name_browse_btn.set_sensitive(True)
        self._remove_widget_items()
        if self.current_main_assistant.name != 'crt' and self.project_name_shown:
            self.box6.remove(self.box_project)
            self.project_name_shown = False
        elif self.current_main_assistant.name == 'crt' and not self.project_name_shown:
            self.box6.remove(self.box_path_main)
            self.box6.pack_start(self.box_project, False, False, 0)
            self.box6.pack_end(self.box_path_main, False, False, 0)
            self.project_name_shown = True
        caption_text = "Project: "
        row = 0
        # get selectected assistants, but without TopAssistant itself
        path = self.top_assistant.get_selected_subassistant_path(**self.kwargs)[1:]
        caption_parts = []

        # Finds any dependencies
        found_deps = [x for x in sorted(path) if x.dependencies()]
        # This bool variable is used for showing text "Available options:"
        any_options = False
        for ass in sorted(path):
            caption_parts.append("<b>" + ass.fullname + "</b>")
            for arg in sorted([x for x in ass.args if not '--name' in x.flags], key=lambda y: y.flags):
                if not (arg.name == "deps_only" and not found_deps):
                    row = self._add_table_row(arg, len(arg.flags) - 1, row) + 1
                    any_options = True
        if not any_options:
            self.title.set_text("")
        else:
            self.title.set_text("Available options:")
        caption_text += ' -> '.join(caption_parts)
        self.label_caption.set_markup(caption_text)
        self.path_window.show_all()
        self.entry_project_name.set_text(os.path.basename(self.kwargs.get('name', '')))
        self.entry_project_name.set_sensitive(True)
        self.run_btn.set_sensitive(not self.project_name_shown or self.entry_project_name.get_text() != "")
        if 'name' in self.kwargs:
            self.dir_name.set_text(os.path.dirname(self.kwargs.get('name', '')))
        for arg in [x for x in self.kwargs if x.title() in self.entries]:
            self.entries[arg.title()].set_text(self.kwargs.get(arg))
        for btn in [x for x in self.button if isinstance(x, Gtk.CheckButton)]:
            lbl = self.gui_helper.get_btn_lower_replace(btn)
            if lbl in self.kwargs and self.kwargs[lbl] != "":
                btn.set_active(True)
                if lbl in self.browse_btns:
                    self.browse_btns[btn.get_label()].set_sensitive(True)
            else:
                btn.set_active(False)

    def _check_box_toggled(self, widget, data=None):
        """
        Function manipulates with entries and buttons.
        """
        active = widget.get_active()
        label = widget.get_label()

        browse_btn = self.browse_btns.get(label)
        if browse_btn and label.lower() != 'github':
            browse_btn.set_sensitive(active)

        for _, entry in [x for x in self.entries.items() if x[0] == label]:
            entry.set_sensitive(active)

        self.path_window.show_all()

    def _deps_only_toggled(self, widget, data=None):
        """
        Function deactivate options in case of deps_only and opposite
        """
        active = widget.get_active()
        self.dir_name.set_sensitive(not active)
        self.entry_project_name.set_sensitive(not active)
        self.dir_name_browse_btn.set_sensitive(not active)
        self.run_btn.set_sensitive(active or not self.project_name_shown or self.entry_project_name.get_text() != "")

    def prev_window(self, widget, data=None):
        """
        Function returns to Main Window
        """
        self.path_window.hide()
        self.parent.open_window(widget, self.data)

    def get_data(self):
        """
        Function returns project dirname and project name
        """
        return self.dir_name.get_text(), self.entry_project_name.get_text()

    def browse_path(self, window):
        """
        Function opens the file chooser dialog for settings project dir
        """
        text = self.gui_helper.create_file_chooser_dialog("Choose project directory", self.path_window, name="Select")
        if text is not None:
            self.dir_name.set_text(text)

    def _check_box_title(self, arg, number):
        """
        Function returns a title from checkbox from args
        """
        return arg.flags[number][2:].title()

    def open_webbrowser(self, widget):
        """
        Function opens webbrowser
        """
        import webbrowser

        webbrowser.open_new_tab(widget.get_uri())

    def _add_table_row(self, arg, number, row):
        """
        Function adds options to a grid
        """
        align = self.gui_helper.create_alignment()
        star_flag = False
        if arg.kwargs.get('required'):
            # If argument is required then red star instead of checkbox
            star_label = self.gui_helper.create_label('<span color="#FF0000">*</span>'.
                                                      format(self._check_box_title(arg, number)))
            star_label.set_padding(0, 3)
            label = self.gui_helper.create_label(self._check_box_title(arg, number))
            box = self.gui_helper.create_box()
            box.pack_start(star_label, False, False, 6)
            box.pack_start(label, False, False, 6)
            align.add(box)
            self.button[label] = arg
            star_flag = True
        else:
            act_btn = self.gui_helper.create_checkbox(self._check_box_title(arg, number))
            act_btn.set_alignment(0, 0)
            self.button[act_btn] = arg
            if arg.name == "deps_only":
                act_btn.connect("clicked", self._deps_only_toggled)
            else:
                act_btn.connect("clicked", self._check_box_toggled)
            align.add(act_btn)
        if row == 0:
            self.grid.add(align)
        else:
            self.grid.attach(align, 0, row, 1, 1)
        label = self.gui_helper.create_label(arg.kwargs['help'], justify=Gtk.Justification.LEFT)
        label.set_alignment(0, 0)
        label.set_padding(0, 3)
        self.grid.attach(label, 1, row, 1, 1)
        label_check_box = self.gui_helper.create_label(name="")
        self.grid.attach(label_check_box, 0, row, 1, 1)
        if arg.get_gui_hint('type') not in ['bool', 'const']:
            new_box = self.gui_helper.create_box(spacing=6)
            entry = self.gui_helper.create_entry(text="")
            align = self.gui_helper.create_alignment()
            align.add(entry)
            new_box.pack_start(align, False, False, 6)
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
            self.link_button = self.gui_helper.create_link_button(text="For registration visit GitHub Homepage",
                                                                  uri="https://www.github.com")
            self.link_button.connect("clicked", self.open_webbrowser)
            entry.set_text(arg.get_gui_hint('default'))
            if arg.kwargs.get('required'):
                self.browse_btn.set_sensitive(True)
                self.link_button.set_sensitive(True)
                entry.set_sensitive(True)
                if not star_flag:
                    act_btn.set_active(True)
                    act_btn.set_sensitive(False)
            else:
                self.browse_btn.set_sensitive(False)
                self.link_button.set_sensitive(False)
                entry.set_sensitive(False)
                act_btn.set_active(False)
            if arg.get_gui_hint('type') == 'path':
                align_btn.add(self.browse_btn)
                self.browse_btns[self._check_box_title(arg, number)] = self.browse_btn
            elif arg.get_gui_hint('type') == 'str':
                if arg.name == 'github' or arg.name == 'github-login':
                    align_btn.add(self.link_button)
                    self.browse_btns[self._check_box_title(arg, number)] = self.link_button
                    self.link_button.set_sensitive(True)
            new_box.pack_start(align_btn, False, False, 6)
            row += 1
            self.entries[self._check_box_title(arg, number)] = entry
            self.grid.attach(new_box, 1, row, 1, 1)
        return row

    def browse_clicked(self, widget, data=None):
        """
        Function sets the directory to entry
        """
        text = self.gui_helper.create_file_chooser_dialog("Please select directory", self.path_window)
        if text is not None:
            data.set_text(text)

    def update_full_label(self):
        """
        Function is used for updating whole path
        of project
        """
        self.label_full_prj_dir.set_text(self.get_full_dir_name())

    def project_name_changed(self, widget, data=None):
        """
        Function controls whether run button is enabled
        """
        if widget.get_text() != "":
            self.run_btn.set_sensitive(True)
        else:
            self.run_btn.set_sensitive(False)
        self.update_full_label()

    def dir_name_changed(self, widget, data=None):
        """
        Function is used for controlling
        label Full Directory project name
        """
        self.update_full_label()