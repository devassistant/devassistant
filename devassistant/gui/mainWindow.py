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

class DevelAssistants(assistant_base.AssistantBase):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants(roles=['creator'])
        return sa


class mainWindow(object):

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile)
        self.mainWin = self.builder.get_object("mainWindow")
        self.pathWindow = pathWindow.pathWindow(self, self.mainWin, self.builder)
        self.finalWindow = finalWindow.finalWindow(self, self.pathWindow, self.builder)
        self.runWindow = runWindow.runWindow(self, self.finalWindow, self.builder, DevelAssistants())
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
                "on_textViewLog_visibility_notify_event" : self.runWindow.visibility_event,
                "on_prevPathBtn_clicked": self.pathWindow.prev_window,
                "on_prevFinalBtn_clicked": self.finalWindow.prev_window,
                "on_runFinalBtn_clicked": self.finalWindow.run_btn,
                    }
        self.builder.connect_signals(self.mainhandlers)
        self.labelMainWindow = self.builder.get_object("sublabel")
        self.labelProjectName = self.builder.get_object("labelProjectName")
        self.box4 = self.builder.get_object("box4")
        self.gridLang = Gtk.Grid()
        self.gridLang.set_column_spacing(12)
        self.gridLang.set_row_spacing(12)
        self.gridLang.set_row_homogeneous(True)
        self.box4.add(self.gridLang)
        self.main, self.subas = DevelAssistants().get_subassistant_chain()
        self.store = Gtk.ListStore(str)
        self.substore = Gtk.ListStore(str)
        self.kwargs = {}
        # Used for debugging
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        logger_gui.addHandler(console_handler)
        # End used for debugging
        row = 0
        column = 0
        for ass in sorted(self.subas, key=lambda x: x[0].fullname):
            if column > 2:
                row += 1
                column = 0
            if not ass[1]:
                self._add_button(ass, row, column)
            else:
                self._add_menu_button(ass, row, column)
            column += 1


        self.mainWin.show_all()
        Gdk.threads_enter()
        Gtk.main()
        Gdk.threads_leave()

    def _create_button(self):
        btn = Gtk.Button()
        return btn

    def _create_label(self, name, justify, wrap):
        label = Gtk.Label()
        name = name.replace(',',',\n').replace('.','.\n')
        label.set_markup(name)
        label.set_justify(justify)
        label.set_line_wrap(wrap)
        return label

    def _add_button(self, ass, row, column):
        btn = self._create_button()
        text = ass[0].description
        if not text:
            text = "No description"
        label = self._create_label("<b>"+ass[0].fullname+"</b>\n\n"+text,
                                    justify=Gtk.Justification.CENTER,
                                    wrap=True)
        btn.add(label)
        btn.connect("clicked", self.btn_clicked, ass[0].name)
        if row == 0 and column == 0:
            self.gridLang.add(btn)
        else:
            self.gridLang.attach(btn, column, row, 1, 1)

    def _add_menu_button(self, ass, row, column):
        btn = self._create_button()
        text = ass[0].description
        if not text:
            text = "No description"
        label = self._create_label("<b>"+ass[0].fullname+"</b>\n\n"+text,
                                    justify=Gtk.Justification.CENTER,
                                    wrap=True)
        btn.add(label)
        menu = Gtk.Menu()
        for ass in filter(lambda x: x[0].fullname == ass[0].fullname, self.subas):
            for sub in sorted(ass[1], key=lambda y: y[0].fullname):
                menu_item = Gtk.MenuItem(sub[0].fullname)
                menu_item.show()
                menu.append(menu_item)
                item = []
                item.append(ass[0].name)
                item.append(sub[0].name)
                menu_item.connect("activate", self.submenu_activate, item)
        logger_gui.info(menu)
        menu.show_all()
        btn.connect_object("event", self.btn_press_event, menu)
        if row == 0 and column == 0:
            self.gridLang.add(btn)
        else:
            self.gridLang.attach(btn, column, row, 1, 1)

    def btn_press_event(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button.button == 1:
                widget.popup(None, None, None, None, event.button.button, event.time)
            return True
        return False

    def submenu_activate(self, widget, item):
        self.kwargs['subassistant_0']=item[0]
        if self.kwargs.has_key('subassistant_1'):
            del (self.kwargs['subassistant_1'])
        self.kwargs['subassistant_1']=item[1]
        self.pathWindow.open_window(widget, data=None)
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
