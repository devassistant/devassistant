#!/usr/bin/env python
import sys
import logging

from gi.repository import Gtk, Gdk
from gi.repository import GLib

from devassistant import assistant_base
from devassistant import yaml_assistant_loader
from devassistant.logger import logger
from devassistant.logger import logger_gui

from devassistant.gui import pathWindow
from devassistant.gui import finalWindow
from devassistant.gui import runWindow

import threading, thread
import gobject

GLib.threads_init()
Gdk.threads_init()

gladefile = "./devassistant/gui/devel-assistant.glade"

class DevelCreatorAssistants(assistant_base.AssistantBase):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants(roles=['creator'])
        return sa

class DevelModifierAssistants(assistant_base.AssistantBase):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants(roles=['modifier'])
        return sa

class DevelPreparerAssistants(assistant_base.AssistantBase):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants(roles=['preparer'])
        return sa


class mainWindow(object):

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.mainWin = self.builder.get_object("mainWindow")
        self.pathWindow = pathWindow.pathWindow(self, self.mainWin, self.builder)
        self.finalWindow = finalWindow.finalWindow(self, self.pathWindow, self.builder)
        self.runWindow = runWindow.runWindow(self, self.finalWindow, self.builder, DevelCreatorAssistants())
        self.mainhandlers = {
                "on_cancelMainBtn_clicked": Gtk.main_quit,
                "on_mainWindow_delete_event": Gtk.main_quit,
                "on_browsePathBtn_clicked": self.pathWindow.browse_path,
                "on_cancelPathBtn_clicked": Gtk.main_quit,
                "on_cancelFinalBtn_clicked": Gtk.main_quit,
                "on_cancelRunBtn_clicked": self.runWindow.close_btn,
                "on_nextPathBtn_clicked": self.pathWindow.next_window,
                "on_pathWindow_delete_event": Gtk.main_quit,
                "on_finalWindow_delete_event": Gtk.main_quit,
                "on_runWindow_delete_event": Gtk.main_quit,
                "on_prevPathBtn_clicked": self.pathWindow.prev_window,
                "on_prevFinalBtn_clicked": self.finalWindow.prev_window,
                "on_runFinalBtn_clicked": self.finalWindow.run_btn,
                    }
        self.builder.connect_signals(self.mainhandlers)
        self.labelMainWindow = self.builder.get_object("sublabel")
        self.labelProjectName = self.builder.get_object("labelProjectName")
        self.box4 = self.builder.get_object("box4")
        self.box4.set_spacing(12)
        self.box4.set_border_width(12)
        # Creating Notebook widget.
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        self.notebook.set_show_border(True)
        self.box4.pack_start(self.notebook, False, False, 12)
        # Devassistant creator part
        self.main, self.subas = DevelCreatorAssistants().get_subassistant_chain()
        self.notebook.append_page(self._create_notebook_page(self.subas, 'Creator'), Gtk.Label('Creator'))
        # Devassistant modifier part
        self.main, self.subas = DevelModifierAssistants().get_subassistant_chain()
        self.notebook.append_page(self._create_notebook_page(self.subas, 'Modifier'), Gtk.Label('Modifier'))
        # Devassistant preparer part
        self.main, self.subas = DevelPreparerAssistants().get_subassistant_chain()
        self.notebook.append_page(self._create_notebook_page(self.subas, 'Preparer'), Gtk.Label('Preparer'))

        self.notebook.show()
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

    def _create_frame(self):
        """
            This function is used for creating general Gtk.Frame
        """
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        return frame
    
    def _create_notebook_page(self, assistant, text=None):
        """
            This function is used for create tab page for notebook.
            Input arguments are:
                assistant - used for collecting all info about assistants and subassistants
                text - used for label of tab page
        """
        frame = self._create_frame()
        gridLang = Gtk.Grid()
        frame.add(gridLang)
        gridLang.set_column_spacing(12)
        gridLang.set_row_spacing(12)
        gridLang.set_border_width(12)
        gridLang.set_row_homogeneous(False)
        row = 0
        column = 0
        for ass in sorted(assistant, key=lambda x: x[0].fullname):
            if column > 2:
                row += 1
                column = 0
            if not ass[1]:
                # If assistant has not any subassistant then create only button
                self._add_button(gridLang, ass, row, column)
            else:
                # If assistant has more subassistants then create button with menu
                self._add_menu_button(gridLang, ass, row, column)
            column += 1
        return frame
    
    def _create_button(self):
        """
        This is generalized method for creating Gtk.Button
        """
        btn = Gtk.Button()
        return btn

    def _create_label(self, name, justify, wrap):
        """
        The function is used for creating lable with HTML text
        """
        label = Gtk.Label()
        name = name.replace(',',',\n').replace('.','.\n')
        label.set_markup(name)
        label.set_justify(justify)
        label.set_line_wrap(wrap)
        return label

    def _tooltip_queries(self, item, x, y, key_mode, tooltip, text):
        """
        The function is used for setting tooltip on menus and submenus
        """
        tooltip.set_text(text)
        return True
    
    def _add_button(self, gridLang, ass, row, column):
        """
        The function is used for creating button with all features
        like signal on tooltip and signal on clicked
        The function does not have any menu.
        Button is add to the Gtk.Grid
        """
        btn = self._create_button()
        #text = ass[0].description
        #if not text:
        #    text = "No description"
        label = self._create_label("<b>"+ass[0].fullname+"</b>\n",
                                    justify=Gtk.Justification.CENTER,
                                    wrap=True)
        btn.add(label)
        if ass[0].description:
            btn.set_has_tooltip(True)
            btn.connect("query-tooltip", self._tooltip_queries, ass[0].description)
        btn.connect("clicked", self.btn_clicked, ass[0].name)
        if row == 0 and column == 0:
            gridLang.add(btn)
        else:
            gridLang.attach(btn, column, row, 1, 1)

    def _add_menu_button(self, gridLang, assistant, row, column):
        """
        The function is used for creating button with menu and submenu.
        Also signal on tooltip and signal on clicked are specified
        Button is add to the Gtk.Grid
        """
        btn = self._create_button()
        menu = Gtk.Menu()
        text=""
        for sub in sorted(assistant[1], key=lambda y: y[0].fullname):
            text+=sub[0].fullname+"\n"
            menu_item = Gtk.MenuItem(sub[0].fullname)
            if sub[0].description:
                menu_item.set_has_tooltip(True)
                menu_item.connect("query-tooltip", self._tooltip_queries, sub[0].description)
            menu_item.show()
            menu.append(menu_item)
            item = []
            item.append(assistant[0].name)
            item.append(sub[0].name)
            menu_item.connect("activate", self.submenu_activate, item)
        menu.show_all()
        label = self._create_label("<b>"+assistant[0].fullname+"</b>\n\n"+text,
                                    justify=Gtk.Justification.CENTER,
                                    wrap=True)
        btn.add(label)
        if assistant[0].description:
            btn.set_has_tooltip(True)
            btn.connect("query-tooltip", self._tooltip_queries, assistant[0].description)
        btn.connect_object("event", self.btn_press_event, menu)
        if row == 0 and column == 0:
            gridLang.add(btn)
        else:
            gridLang.attach(btn, column, row, 1, 1)

    def btn_press_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 3:
                widget.popup(None, None, None, None, event.button.button, event.time)
            return True
        return False

    def submenu_activate(self, widget, item):
        self.kwargs['subassistant_0']=item[0]
        if self.kwargs.has_key('subassistant_1'):
            del (self.kwargs['subassistant_1'])
        self.kwargs['subassistant_1']=item[1]
        self.pathWindow.open_window(widget, data=item)
        self.mainWin.hide()
    
    def btn_clicked(self, widget, data=None):
        self.kwargs['subassistant_0']=data
        if self.kwargs.has_key('sub_assistant_1'):
            del (self.kwargs['sub_assistnant_1'])
        self.pathWindow.open_window(widget, data=None)
        self.mainWin.hide()

    def browse_path(self, window):
        self.pathWindow.browsePath()

    def open_window(self, widget, data=None):
        self.mainWin.show_all()
