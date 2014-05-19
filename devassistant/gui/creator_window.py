#!/usr/bin/env python
import sys
import logging

from gi.repository import Gtk, Gdk
from gi.repository import GLib

from devassistant.bin import CreatorAssistant
from devassistant.logger import logger_gui
from devassistant.gui import gui_helper
from devassistant.gui import yaml_window

GLib.threads_init()
Gdk.threads_init()

gladefile = "./devassistant/gui/devel-yaml.glade"

class CreatorWindow(object):

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.main_win = self.builder.get_object("mainWindow")
        self.gui_helper = gui_helper.GuiHelper(self)
        self.yaml_window = yaml_window.YamlWindow(self, self.main_win, self.builder)
        #self.finalWindow = finalWindow.finalWindow(self, self.pathWindow, self.builder)
        #self.runWindow = runWindow.runWindow(self, self.finalWindow, self.builder, DevelCreatorAssistants())
        self.mainhandlers = {
                "on_cancelMainBtn_clicked": Gtk.main_quit,
                "on_mainWindow_delete_event": Gtk.main_quit,
                "on_cancelYamlBtn_clicked": Gtk.main_quit,
                "on_yamlWindow_delete_event": Gtk.main_quit,
                "on_prevYamlBtn_clicked": self.yaml_window.prev_window,
                "on_createYamlBtn_clicked": self.yaml_window.run_btn,
                    }
        self.builder.connect_signals(self.mainhandlers)
        self.label_main_window = self.builder.get_object("sublabel")
        self.label_project_name = self.builder.get_object("labelProjectName")
        self.box4 = self.builder.get_object("box4")
        self.box4.set_spacing(12)
        self.box4.set_border_width(12)
        # Creating Notebook widget.
        # Devassistant creator part
        self.main, self.subas = CreatorAssistant().get_subassistant_tree()
        scrolled_window = self._create_notebook_page(self.subas, 'Creator')
        self.box4.pack_start(scrolled_window, True, True, 0)

        self.kwargs = {}
        # Used for debugging
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        logger_gui.addHandler(console_handler)
        # End used for debugging

        self.main_win.show_all()
        Gdk.threads_enter()
        Gtk.main()
        Gdk.threads_leave()

    def _create_notebook_page(self, assistant, text=None):
        """
            This function is used for create tab page for notebook.
            Input arguments are:
                assistant - used for collecting all info about assistants and subassistants
                text - used for label of tab page
        """
        #frame = self._create_frame()
        grid_lang = self.gui_helper.create_gtk_grid()
        scrolled_window = self.gui_helper.create_scrolled_window(grid_lang)
        row = 0
        column = 0
        for ass in sorted(assistant, key=lambda x: x[0].fullname.lower()):
            if column > 2:
                row += 1
                column = 0
            if not ass[1]:
                # If assistant has not any subassistant then create only button
                self.gui_helper.add_button(grid_lang, ass, row, column)
            else:
                # If assistant has more subassistants then create button with menu
                self.gui_helper.add_menu_button(grid_lang, ass, row, column)
            column += 1
        # empty assistant
        if column > 2:
            row+=1
            column = 0
        btn=self.gui_helper.button_with_label("<b>New assistant</b>")
        btn.connect("clicked", self.btn_clicked, "new_assistant")
        if row == 0 and column == 0:
            grid_lang.add(btn)
        else:
            grid_lang.attach(btn, column, row, 1, 1)

        return scrolled_window

    def _tooltip_queries(self, item, x, y, key_mode, tooltip, text):
        """
        The function is used for setting tooltip on menus and submenus
        """
        tooltip.set_text(text)
        return True

    def submenu_activate(self, widget, item):
        self.kwargs['subassistant_0']=item[0]
        if 'subassistant_1' in self.kwargs:
            del (self.kwargs['subassistant_1'])
        self.kwargs['subassistant_1']=item[1]
        self.kwargs['eclipse']=None
        self.kwargs['vim']=None
        self.kwargs['github']=None
        self.yaml_window.open_window(widget, self.kwargs)
        self.main_win.hide()

    def btn_clicked(self, widget, data=None):
        self.kwargs['subassistant_0']=data
        if 'subassistant_1' in self.kwargs:
            del (self.kwargs['subassistant_1'])
        self.yaml_window.open_window(widget, self.kwargs)
        self.main_win.hide()

    def open_window(self, widget, data=None):
        self.main_win.show_all()

    def btn_press_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 1:
                widget.popup(None, None, None, None, event.button.button, event.time)
            return True
        return False

