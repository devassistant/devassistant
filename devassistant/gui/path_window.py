# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 13:16:47 2013

@author: Petr Hracek
"""

import os
from gi.repository import Gtk
from devassistant.config_manager import config_manager
from devassistant import utils


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
        self.args = dict()
        self.grid = self.gui_helper.create_gtk_grid(row_spacing=0,
                                                    col_homogenous=False,
                                                    row_homogenous=False)
        self.title = self.gui_helper.create_label("Available options:")
        self.title.set_alignment(0, 0)
        self.box_path_main.pack_start(self.title, False, False, 0)
        self.box_path_main.pack_start(self.grid, False, False, 0)
        self.kwargs = dict()
        self.label_caption = self.builder.get_object("labelCaption")
        self.label_prj_name = self.builder.get_object("labelPrjName")
        self.label_prj_dir = self.builder.get_object("labelPrjDir")
        self.label_full_prj_dir = self.builder.get_object("labelFullPrjDir")
        self.h_separator = self.builder.get_object("hseparator")
        self.top_assistant = None
        self.project_name_shown = True
        self.current_main_assistant = None
        self.data = dict()

    def arg_is_selected(self, arg_dict):
        if arg_dict['arg'].kwargs.get('required'):
            return True
        else:
            return arg_dict['checkbox'].get_active()

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
        deps_only = ('deps_only' in self.args and self.args['deps_only']['checkbox'].get_active())

        # preserve argument value if it is needed to be preserved
        for arg_dict in [x for x in self.args.values() if 'preserved' in x['arg'].kwargs]:
            preserve_key = arg_dict['arg'].kwargs['preserved']
            # preserve entry text (string value)
            if 'entry' in arg_dict:
                if self.arg_is_selected(arg_dict):
                    config_manager.set_config_value(preserve_key, arg_dict['entry'].get_text())
            # preserve if checkbox is ticked (boolean value)
            else:
                config_manager.set_config_value(preserve_key, self.arg_is_selected(arg_dict))

        # save configuration into file
        config_manager.save_configuration_file()
        # get project directory and name
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
        self.kwargs['__ui__'] = 'gui_gtk+'

        self.data['kwargs'] = self.kwargs
        self.data['top_assistant'] = self.top_assistant
        self.data['current_main_assistant'] = self.current_main_assistant
        self.parent.run_window.open_window(widget, self.data)
        self.path_window.hide()

    def _build_flags(self):
        """
        Function builds kwargs variable for run_window
        """
        # Check if all entries for selected arguments are nonempty
        for arg_dict in [x for x in self.args.values() if self.arg_is_selected(x)]:
            if 'entry' in arg_dict and not arg_dict['entry'].get_text():
                self.gui_helper.execute_dialog("Entry {0} is empty".format(arg_dict['label']))
                return False

        # Check for active CheckButtons
        for arg_dict in [x for x in self.args.values() if self.arg_is_selected(x)]:
            arg_name = arg_dict['arg'].get_dest()
            if 'entry' in arg_dict:
                self.kwargs[arg_name] = arg_dict['entry'].get_text()
            else:
                if arg_dict['arg'].get_gui_hint('type') == 'const':
                    self.kwargs[arg_name] = arg_dict['arg'].kwargs['const']
                else:
                    self.kwargs[arg_name] = True

        # Check for non active CheckButtons but with defaults flag
        for arg_dict in [x for x in self.args.values() if not self.arg_is_selected(x)]:
            arg_name = arg_dict['arg'].get_dest()
            if 'default' in arg_dict['arg'].kwargs:
                self.kwargs[arg_name] = arg_dict['arg'].get_gui_hint('default')
            elif arg_name in self.kwargs:
                del self.kwargs[arg_name]

        return True

    def _remove_widget_items(self):
        """
        Function removes widgets from grid
        """
        for btn in self.grid:
            self.grid.remove(btn)

    def get_default_project_dir(self):
        """Returns a project directory to prefill in GUI.
        It is either stored value or current directory (if exists) or home directory.
        """
        ret = config_manager.get_config_value('da.project_dir')
        return ret or utils.get_cwd_or_homedir()

    def open_window(self, data=None):
        """
        Function opens the Options dialog
        """
        self.args = dict()
        if data is not None:
            self.top_assistant = data.get('top_assistant', None)
            self.current_main_assistant = data.get('current_main_assistant', None)
            self.kwargs = data.get('kwargs', None)
            self.data['debugging'] = data.get('debugging', False)
        project_dir = self.get_default_project_dir()
        self.dir_name.set_text(project_dir)
        self.label_full_prj_dir.set_text(project_dir)
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
        found_deps = [x for x in path if x.dependencies()]
        # This bool variable is used for showing text "Available options:"
        any_options = False
        for assistant in path:
            caption_parts.append("<b>" + assistant.fullname + "</b>")
            for arg in sorted([x for x in assistant.args if not '--name' in x.flags], key=lambda y: y.flags):
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
        for arg_name, arg_dict in [(k, v) for (k, v) in self.args.items() if self.kwargs.get(k)]:
            if 'checkbox' in arg_dict:
                arg_dict['checkbox'].set_active(True)
            if 'entry' in arg_dict:
                arg_dict['entry'].set_sensitive(True)
                arg_dict['entry'].set_text(self.kwargs[arg_name])
            if 'browse_btn' in arg_dict:
                arg_dict['browse_btn'].set_sensitive(True)

    def _check_box_toggled(self, widget, data=None):
        """
        Function manipulates with entries and buttons.
        """
        active = widget.get_active()
        arg_name = data

        if 'entry' in self.args[arg_name]:
            self.args[arg_name]['entry'].set_sensitive(active)
        if 'browse_btn' in self.args[arg_name]:
            self.args[arg_name]['browse_btn'].set_sensitive(active)

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

    def _add_table_row(self, arg, number, row):
        """
        Function adds options to a grid
        """
        self.args[arg.name] = dict()
        self.args[arg.name]['arg'] = arg
        check_box_title = arg.flags[number][2:].title()
        self.args[arg.name]['label'] = check_box_title
        align = self.gui_helper.create_alignment()
        if arg.kwargs.get('required'):
            # If argument is required then red star instead of checkbox
            star_label = self.gui_helper.create_label('<span color="#FF0000">*</span>')
            star_label.set_padding(0, 3)
            label = self.gui_helper.create_label(check_box_title)
            box = self.gui_helper.create_box()
            box.pack_start(star_label, False, False, 6)
            box.pack_start(label, False, False, 6)
            align.add(box)
        else:
            chbox = self.gui_helper.create_checkbox(check_box_title)
            chbox.set_alignment(0, 0)
            if arg.name == "deps_only":
                chbox.connect("clicked", self._deps_only_toggled)
            else:
                chbox.connect("clicked", self._check_box_toggled, arg.name)
            align.add(chbox)
            self.args[arg.name]['checkbox'] = chbox
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
            entry.set_text(arg.get_gui_hint('default'))
            entry.set_sensitive(arg.kwargs.get('required') == True)

            if arg.get_gui_hint('type') == 'path':
                browse_btn = self.gui_helper.button_with_label("Browse")
                browse_btn.connect("clicked", self.browse_clicked, entry)
                browse_btn.set_sensitive(arg.kwargs.get('required') == True)
                align_btn.add(browse_btn)
                self.args[arg.name]['browse_btn'] = browse_btn
            elif arg.get_gui_hint('type') == 'str':
                if arg.name == 'github' or arg.name == 'github-login':
                    link_button = self.gui_helper.create_link_button(text="For registration visit GitHub Homepage",
                                                                     uri="https://www.github.com")
                    align_btn.add(link_button)
            new_box.pack_start(align_btn, False, False, 6)
            row += 1
            self.args[arg.name]['entry'] = entry
            self.grid.attach(new_box, 1, row, 1, 1)
        else:
            if 'preserved' in arg.kwargs and config_manager.get_config_value(arg.kwargs['preserved']):
                if 'checkbox' in self.args[arg.name]:
                    self.args[arg.name]['checkbox'].set_active(True)
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
        and storing current project directory
        in configuration manager
        """
        config_manager.set_config_value("da.project_dir", self.dir_name.get_text())
        self.update_full_label()
