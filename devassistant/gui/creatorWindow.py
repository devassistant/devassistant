#!/usr/bin/env python
import sys
import logging

from gi.repository import Gtk, Gdk
from gi.repository import GLib

from devassistant import assistant_base
from devassistant.bin import CreatorAssistant
from devassistant import yaml_assistant_loader
from devassistant.logger import logger_gui
from devassistant.gui import gui_helper
from devassistant.gui import yamlWindow

import threading, thread
import gobject

GLib.threads_init()
Gdk.threads_init()

gladefile = "./devassistant/gui/devel-yaml.glade"

class creatorWindow(object):

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.mainWin = self.builder.get_object("mainWindow")
        self.gui_helper = gui_helper.gui_helper(self)
        self.yamlWindow = yamlWindow.yamlWindow(self, self.mainWin, self.builder)
        #self.finalWindow = finalWindow.finalWindow(self, self.pathWindow, self.builder)
        #self.runWindow = runWindow.runWindow(self, self.finalWindow, self.builder, DevelCreatorAssistants())
        self.mainhandlers = {
                "on_cancelMainBtn_clicked": Gtk.main_quit,
                "on_mainWindow_delete_event": Gtk.main_quit,
                "on_cancelYamlBtn_clicked": Gtk.main_quit,
                "on_yamlWindow_delete_event": Gtk.main_quit,
                "on_prevYamlBtn_clicked": self.yamlWindow.prev_window,
                "on_createYamlBtn_clicked": self.yamlWindow.run_btn,
                    }
        self.builder.connect_signals(self.mainhandlers)
        self.labelMainWindow = self.builder.get_object("sublabel")
        self.labelProjectName = self.builder.get_object("labelProjectName")
        self.box4 = self.builder.get_object("box4")
        self.box4.set_spacing(12)
        self.box4.set_border_width(12)
        # Creating Notebook widget.
        # Devassistant creator part
        self.main, self.subas = CreatorAssistant().get_subassistant_tree()
        scrolledWindow = self._create_notebook_page(self.subas, 'Creator')
        self.box4.pack_start(scrolledWindow, True, True, 0)

        self.kwargs = {}
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
        # empty assistant
        btn=self.gui_helper.button_with_label("<b>New assistant</b>")
        btn.connect("clicked", self.btn_clicked, "new_assistant")
        if row == 0 and column == 0:
            gridLang.add(btn)
        else:
            gridLang.attach(btn, column, row, 1, 1)

        return scrolledWindow

    def _tooltip_queries(self, item, x, y, key_mode, tooltip, text):
        """
        The function is used for setting tooltip on menus and submenus
        """
        tooltip.set_text(text)
        return True

    def submenu_activate(self, widget, item):
        self.kwargs['subassistant_0']=item[0]
        if self.kwargs.has_key('subassistant_1'):
            del (self.kwargs['subassistant_1'])
        self.kwargs['subassistant_1']=item[1]
        self.kwargs['eclipse']=None
        self.kwargs['vim']=None
        self.kwargs['github']=None
        self.yamlWindow.open_window(widget, self.kwargs)
        self.mainWin.hide()

    def btn_clicked(self, widget, data=None):
        self.kwargs['subassistant_0']=data
        if self.kwargs.has_key('subassistant_1'):
            del (self.kwargs['subassistant_1'])
        self.yamlWindow.open_window(widget, self.kwargs)
        self.mainWin.hide()

    def open_window(self, widget, data=None):
        self.mainWin.show_all()

    def btn_press_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 1:
                widget.popup(None, None, None, None, event.button.button, event.time)
            return True
        return False

