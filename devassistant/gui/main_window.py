#!/usr/bin/env python
"""
This is a main module of DevAssistant GUI
It shows main window with all assistants and all
devassistant types.
"""
import os
import sys
import logging

from gi.repository import Gtk, Gdk
from gi.repository import GLib

from devassistant.bin import TopAssistant
from devassistant import logger
from devassistant import settings
from devassistant.config_manager import config_manager

from devassistant.gui import path_window
from devassistant.gui import run_window
from devassistant.gui import gui_helper

GLADE_FILE = os.path.join(os.path.dirname(__file__), 'devel-assistant.glade')


class MainWindow(object):
    """
    The main window takes care about showing glade file and
    selecting kind devassistant and type
    """

    def __init__(self):
        # Used for debugging
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        logger.logger_gui.addHandler(console_handler)
        # End used for debugging
        # Setup logger for warnings and errors that can occur before running assistants
        #  (e.g. errors from loading faulty assistants)
        # TODO: are the logger.Devassistant* classes good enough or do we need special ones?
        ch = logger.DevassistantClHandler(stream=sys.stderr)
        ch.setFormatter(logger.DevassistantClFormatter())
        ch.setLevel(logging.WARNING)
        logger.logger.addHandler(ch)
        # End setup logger
        self.builder = Gtk.Builder()
        self.builder.add_from_file(GLADE_FILE)
        self.main_win = self.builder.get_object("mainWindow")
        self.gui_helper = gui_helper.GuiHelper(self)
        self.path_window = path_window.PathWindow(self,
                                                  self.main_win,
                                                  self.builder,
                                                  self.gui_helper)
        self.run_window = run_window.RunWindow(self,
                                               self.builder,
                                               self.gui_helper)
        self.main_handlers = {
            "on_mainWindow_delete_event": self.delete_event,
            "on_browsePathBtn_clicked": self.path_window.browse_path,
            "on_nextPathBtn_clicked": self.path_window.next_window,
            "on_pathWindow_delete_event": self.delete_event,
            "on_runWindow_delete_event": self.run_window.delete_event,
            "on_runWindow_destroy": self.run_window.destroy,
            "on_prevPathBtn_clicked": self.path_window.prev_window,
            "on_debugBtn_clicked": self.run_window.debug_btn_clicked,
            "on_clipboardBtn_clicked": self.run_window.clipboard_btn_clicked,
            "on_backBtn_clicked": self.run_window.back_btn_clicked,
            "on_mainBtn_clicked": self.run_window.main_btn_clicked,
            "on_entryProjectName_changed": self.path_window.project_name_changed,
            "on_dirName_changed": self.path_window.dir_name_changed,
        }
        self.builder.connect_signals(self.main_handlers)
        self.label_main_window = self.builder.get_object("sublabel")
        self.label_project_name = self.builder.get_object("labelProjectName")
        self.box4 = self.builder.get_object("box4")
        self.box4.set_spacing(12)
        self.box4.set_border_width(12)
        # Creating Notebook widget.
        self.notebook = self.gui_helper.create_notebook()
        self.notebook.set_has_tooltip(True)
        self.box4.pack_start(self.notebook, True, True, 0)
        # Devassistant creator part
        self.top_assistant = TopAssistant()
        for sub_as in self.top_assistant.get_subassistants():
            tool_tip = self.gui_helper.get_formatted_description(sub_as.description)
            label = self.gui_helper.create_label(
                sub_as.fullname,
                wrap_mode=False,
                tooltip=tool_tip
            )
            self.notebook.append_page(self._create_notebook_page(sub_as), label)

        self.notebook.show()
        self.kwargs = dict()
        self.data = dict()
        self.dev_assistant_path = []
        self.main_win.show_all()
        # Load configuration file
        config_manager.load_configuration_file()
        # Thread should be defined here
        # because of timeout and threads sharing.
        GLib.threads_init()
        Gdk.threads_init()
        Gdk.threads_enter()
        Gtk.main()
        Gdk.threads_leave()

    def tooltip_queries(self, item, x_coord, y_coord, key_mode, tooltip, text):
        """
        The function is used for setting tooltip on menus and submenus
        """
        tooltip.set_text(text)
        return True

    def _create_notebook_page(self, assistant):
        """
        This function is used for create tab page for notebook.
        Input arguments are:
        assistant - used for collecting all info about assistants and subassistants
        """
        #frame = self._create_frame()
        grid_lang = self.gui_helper.create_gtk_grid()
        scrolled_window = self.gui_helper.create_scrolled_window(grid_lang)
        row = 0
        column = 0
        scrolled_window.main_assistant, sub_as = assistant.get_subassistant_tree()
        for ass in sorted(sub_as, key=lambda x: x[0].fullname.lower()):
            if column > 2:
                row += 1
                column = 0
            if not ass[1]:
                # If assistant has not any subassistant then create only button
                self.gui_helper.add_button(grid_lang, ass, row, column)
            else:
                # If assistant has more subassistants then create button with menu
                self.gui_helper.add_submenu(grid_lang, ass, row, column)
            column += 1

        # Install More Assistants button
        if column > 2:
            row += 1
            column = 0
        self.gui_helper.add_install_button(grid_lang, row, column)
        column += 1

        if row == 0 and len(sub_as) < 3:
            while column < 3:
                btn = self.gui_helper.create_button(style=Gtk.ReliefStyle.NONE)
                btn.set_sensitive(False)
                btn.hide()
                grid_lang.attach(btn, column, row, 1, 1)
                column += 1
        return scrolled_window

    def sub_menu_select(self, widget, item):
        """
        If any menu is selected then store the full path to class
        """
        self.dev_assistant_path = list(item)

    def _open_path_window(self):
        """
        Hides this window and opens path window.
        Passes all needed data and kwargs.
        """
        self.data['top_assistant'] = self.top_assistant
        self.data['current_main_assistant'] = self.get_current_main_assistant()
        self.data['kwargs'] = self.kwargs
        self.path_window.open_window(self.data)
        self.main_win.hide()

    def sub_menu_pressed(self, widget, event):
        """
        Function serves for getting full assistant path and
        collects the information from GUI
        """
        for index, data in enumerate(self.dev_assistant_path):
            index += 1
            if settings.SUBASSISTANT_N_STRING.format(index) in self.kwargs:
                del self.kwargs[settings.SUBASSISTANT_N_STRING.format(index)]
            self.kwargs[settings.SUBASSISTANT_N_STRING.format(index)] = data
        self.kwargs['subassistant_0'] = self.get_current_main_assistant().name
        self._open_path_window()

    def get_current_main_assistant(self):
        """
        Function return current assistant
        """
        current_page = self.notebook.get_nth_page(self.notebook.get_current_page())
        return current_page.main_assistant

    def btn_clicked(self, widget, data=None):
        """
        Function is used for case that assistant does not have any
        subassistants
        """
        self.kwargs['subassistant_0'] = self.get_current_main_assistant().name
        self.kwargs['subassistant_1'] = data
        if 'subassistant_2' in self.kwargs:
            del self.kwargs['subassistant_2']
        self._open_path_window()

    def install_btn_clicked(self, data=None):
#        self.install_window.open_window()
        text = 'To install new Assistants from the DevAssistant Package Index, ' \
               'you must go to the terminal and run "da pkg install [PACKAGE]" ' \
               '(without the quotation marks), where [PACKAGE] is the name of ' \
               'the package you want to install.\n\n' \
               'If you do not know what package you are looking for, use\n"da '\
               'pkg search [NAME]", or browse the Index at ' \
               'https://dapi.devassistant.org.\n\n' \
               'This is a temporary measure, you will be able to install Assistants ' \
               'from the GUI soon.'
        dialog = self.gui_helper.create_message_dialog(text, buttons=Gtk.ButtonsType.OK, icon=Gtk.MessageType.WARNING)
        dialog.run()
        dialog.destroy()


    def browse_path(self, window):
        self.path_window.browse_path()

    def open_window(self, widget, data=None):
        """
        Function opens Main Window and in case of previously created
        project is switches to /home directory
        This is fix in case that da creats a project
        and project was deleted and GUI was not closed yet
        """
        if data is not None:
            self.data = data
        os.chdir(os.path.expanduser('~'))
        self.kwargs = dict()
        self.main_win.show_all()

    def btn_press_event(self, widget, event):
        """
        Function is used for showing Popup menu
        """
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 1:
                widget.popup(None, None, None, None,
                             event.button.button, event.time)
            return True
        return False

    def delete_event(self, widget, event, data=None):
        config_manager.save_configuration_file()
        Gtk.main_quit()
