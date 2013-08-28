#!/usr/bin/env python
import os
import sys
import logging

from gi.repository import Gtk, Gdk
from gi.repository import GLib

from devassistant import assistant_base
from devassistant.bin import CreatorAssistant
from devassistant.bin import ModifierAssistant
from devassistant.bin import PreparerAssistant
from devassistant import yaml_assistant_loader
from devassistant.logger import logger
from devassistant.logger import logger_gui

from devassistant.gui import pathWindow
from devassistant.gui import runWindow
from devassistant.gui import gui_helper

import threading, thread

GLib.threads_init()
Gdk.threads_init()

gladefile = os.path.join(os.path.dirname(__file__), 'devel-assistant.glade')

class mainWindow(object):

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.mainWin = self.builder.get_object("mainWindow")
        self.gui_helper = gui_helper.gui_helper(self)
        self.pathWindow = pathWindow.pathWindow(self, self.mainWin, self.builder, self.gui_helper)
        self.runWindow = runWindow.runWindow(self, self.builder, self.gui_helper)
        self.mainhandlers = {
                "on_cancelMainBtn_clicked": Gtk.main_quit,
                "on_mainWindow_delete_event": Gtk.main_quit,
                "on_browsePathBtn_clicked": self.pathWindow.browse_path,
                "on_cancelPathBtn_clicked": Gtk.main_quit,
                "on_cancelFinalBtn_clicked": Gtk.main_quit,
                "on_cancelRunBtn_clicked": self.runWindow.close_btn,
                "on_nextPathBtn_clicked": self.pathWindow.next_window,
                "on_pathWindow_delete_event": Gtk.main_quit,
                "on_runWindow_delete_event": self.runWindow.close_btn,
                "on_prevPathBtn_clicked": self.pathWindow.prev_window,
                    }
        self.builder.connect_signals(self.mainhandlers)
        self.labelMainWindow = self.builder.get_object("sublabel")
        self.labelProjectName = self.builder.get_object("labelProjectName")
        self.box4 = self.builder.get_object("box4")
        self.box4.set_spacing(12)
        self.box4.set_border_width(12)
        # Creating Notebook widget.
        self.notebook = self.gui_helper.create_notebook()
        self.notebook.set_has_tooltip(True)
        self.box4.pack_start(self.notebook, True, True, 0)
        # Devassistant creator part
        self.main, self.subasCreator = CreatorAssistant().get_subassistant_tree()
        self.notebook.append_page(self._create_notebook_page(self.subasCreator, 'Creator'),
                                  self.gui_helper.create_label(
                                  "Creator",
                                  tooltip=self.gui_helper.get_formated_description(self.main.description)))
        # Devassistant modifier part
        self.main, self.subasModifier = ModifierAssistant().get_subassistant_tree()
        self.notebook.append_page(self._create_notebook_page(self.subasModifier, 'Modifier'),
                                  self.gui_helper.create_label(
                                  'Modifier',
                                  tooltip=self.gui_helper.get_formated_description(self.main.description)))
        # Devassistant preparer part
        self.main, self.subasPreparer = PreparerAssistant().get_subassistant_tree()
        self.notebook.append_page(self._create_notebook_page(self.subasPreparer, 'Preparer'),
                                  self.gui_helper.create_label(
                                  'Preparer',
                                  tooltip=self.gui_helper.get_formated_description(self.main.description)))

        self.notebook.show()
        self.kwargs = dict()
        self.data = dict()
        # Used for debugging
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        logger_gui.addHandler(console_handler)
        # End used for debugging

        self.mainWin.show_all()
        Gdk.threads_enter()
        Gtk.main()
        Gdk.threads_leave()

    def _tooltip_queries(self, item, x, y, key_mode, tooltip, text):
        """
        The function is used for setting tooltip on menus and submenus
        """
        tooltip.set_text(text)
        return True

    def _create_notebook_page(self, assistant, text=None):
        """
            This function is used for create tab page for notebook.
            Input arguments are:
                assistant - used for collecting all info about assistants and subassistants
                text - used for label of tab page
        """
        #frame = self._create_frame()
        gridLang = self.gui_helper.create_gtk_grid()
        scrolledWindow = self.gui_helper.create_scrolled_window(gridLang)
        row = 0
        column = 0
        for ass in sorted(assistant, key=lambda x: x[0].fullname):
            if column > 2:
                row += 1
                column = 0
            if not ass[1]:
                # If assistant has not any subassistant then create only button
                self.gui_helper.add_button(gridLang, ass, row, column)
            else:
                # If assistant has more subassistants then create button with menu
                self.gui_helper.add_menu_button(gridLang, ass, row, column)
            column += 1
        if row == 0 and len(assistant)< 3:
            while column < 3:
                btn = self.gui_helper.create_button(style=Gtk.ReliefStyle.NONE)
                btn.set_sensitive(False)
                btn.hide()
                gridLang.attach(btn, column, row, 1, 1)
                column += 1
        return scrolledWindow

    def submenu_activate(self, widget, item):
        self.kwargs['subassistant_0']=item[0]
        if self.kwargs.has_key('subassistant_1'):
            del (self.kwargs['subassistant_1'])
        self.kwargs['subassistant_1']=item[1]
        self.assistant_selection(self.notebook.get_current_page())
        self.pathWindow.open_window(widget)
        self.mainWin.hide()

    def btn_clicked(self, widget, data=None):
        self.kwargs['subassistant_0']=data
        if self.kwargs.has_key('subassistant_1'):
            del (self.kwargs['subassistant_1'])
        self.assistant_selection(self.notebook.get_current_page())
        self.pathWindow.open_window(widget)
        self.mainWin.hide()

    def browse_path(self, window):
        self.pathWindow.browsePath()

    def open_window(self, widget, data=None):
        self.mainWin.show_all()

    def assistant_selection(self, page):
        self.data['AssistantType']=page
        if page == 0:
            self.assistant_class = CreatorAssistant()
            self.subass = self.subasCreator
        elif page == 1:
            self.assistant_class = ModifierAssistant()
            self.subass = self.subasModifier
        else:
            self.assistant_class = PreparerAssistant()
            self.subass = self.subasPreparer

    def btn_press_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 1:
                widget.popup(None, None, None, None, event.button.button, event.time)
            return True
        return False
