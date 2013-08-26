#!/usr/bin/env python
import sys
import logging

from gi.repository import Gtk, Gdk
from gi.repository import GLib

class gui_helper(object):
    def __init__(self, parent):
        """This is general class for creating GUI
        """
        self.parent = parent

    def create_frame(self):
        """
            This function is used for creating general Gtk.Frame
        """
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        return frame

    def button_with_label(self, description, sensitive=True):
        btn = self.create_button()
        label = self.create_label(description)
        align = self.create_alignment(xalign=0.5, xscale=1)
        align.add(label)
        btn.add(align)
        return btn

    def checkbutton_with_label(self, description):
        actBtn = Gtk.CheckButton(description)
        align = self.create_alignment()
        #align.add(actBtn)
        actBtn.add(align)
        return align

    def create_entry(self, text="", sensitive="False"):
        textEntry = Gtk.Entry()
        textEntry.set_sensitive(sensitive)
        textEntry.set_text(text)
        return textEntry

    def create_link_button(self, text="None", uri="None"):
        linkbtn = Gtk.LinkButton(uri, text)
        return linkbtn;


    def create_button(self):
        """
        This is generalized method for creating Gtk.Button
        """
        btn = Gtk.Button()
        return btn

    def create_checkbutton(self, text=""):
        """
        This is generalized method for creating Gtk.Button
        """
        btn = Gtk.CheckButton()
        return btn

    def create_label(self, name, justify=Gtk.Justification.CENTER, wrap=True, tooltip=None):
        """
        The function is used for creating lable with HTML text
        """
        label = Gtk.Label()
        name = name.replace(',','\n').replace('.','\n')
        label.set_markup(name)
        label.set_justify(justify)
        label.set_line_wrap(wrap)
        if tooltip is not None:
            label.set_has_tooltip(True)
            label.connect("query-tooltip", self.parent._tooltip_queries, tooltip)
        return label

    def add_button(self, gridLang, ass, row, column):
        """
        The function is used for creating button with all features
        like signal on tooltip and signal on clicked
        The function does not have any menu.
        Button is add to the Gtk.Grid
        """
        #print "gui_helper add_button"
        btn = self.button_with_label("<b>"+ass[0].fullname+"</b>")
        #print "Dependencies button",ass[0]._dependencies
        #print "Run button",ass[0]._run
        if ass[0].description:
            btn.set_has_tooltip(True)
            btn.connect("query-tooltip",
                        self.parent._tooltip_queries,
                        self.get_formated_description(ass[0].description)
                        )
        btn.connect("clicked", self.parent.btn_clicked, ass[0].name)
        if row == 0 and column == 0:
            gridLang.add(btn)
        else:
            gridLang.attach(btn, column, row, 1, 1)
        return btn

    def add_menu_button(self, gridLang, assistant, row, column):
        """
        The function is used for creating button with menu and submenu.
        Also signal on tooltip and signal on clicked are specified
        Button is add to the Gtk.Grid
        """
        #print "gui_helper add_menu_button"
        menu = Gtk.Menu()
        text=""
        for sub in sorted(assistant[1], key=lambda y: y[0].fullname):
            text+=sub[0].fullname+","
            menu_item = Gtk.MenuItem(sub[0].fullname)
            if sub[0].description:
                menu_item.set_has_tooltip(True)
                menu_item.connect("query-tooltip",
                                  self.parent._tooltip_queries,
                                  self.get_formated_description(sub[0].description),
                                  )
            menu_item.show()
            menu.append(menu_item)
            item = list()
            item.append(assistant[0].name)
            item.append(sub[0].name)
            menu_item.connect("activate", self.parent.submenu_activate, item)
        menu.show_all()
        btn = self.button_with_label("<b>"+assistant[0].fullname+"</b>\n\n"+text)
        if assistant[0].description:
            btn.set_has_tooltip(True)
            btn.connect("query-tooltip",
                        self.parent._tooltip_queries,
                        self.get_formated_description(assistant[0].description),
                        )
        btn.connect_object("event", self.parent.btn_press_event, menu)
        if row == 0 and column == 0:
            gridLang.add(btn)
        else:
            gridLang.attach(btn, column, row, 1, 1)
        return btn

    def get_formated_description(self, description):
        import re
        text = re.sub(r"\s+",' ',description.split('.')[0])+" "+description.split('.')[1].lstrip()
        from textwrap import wrap
        formatted_text = ""
        for t in wrap(text,60):
            formatted_text = formatted_text + t +"\n"
        return formatted_text

    def create_scrolled_window(self, layout_manager, horizontal=Gtk.PolicyType.NEVER, vertical=Gtk.PolicyType.ALWAYS):
        scrolledWindow = Gtk.ScrolledWindow()
        scrolledWindow.add(layout_manager)
        scrolledWindow.set_policy(horizontal, vertical)
        return scrolledWindow

    def create_gtk_grid(self, row_spacing=6, col_spacing=6, row_homogenous=False,col_homogenous=True):
        gridLang = Gtk.Grid()
        gridLang.set_column_spacing(row_spacing)
        gridLang.set_row_spacing(col_spacing)
        gridLang.set_border_width(6)
        gridLang.set_row_homogeneous(row_homogenous)
        gridLang.set_column_homogeneous(col_homogenous)
        return gridLang

    def create_notebook(self, position=Gtk.PositionType.TOP):
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(position)
        notebook.set_show_border(True)
        return notebook

    def create_message_dialog(self, text, buttons=Gtk.ButtonsType.CLOSE):
        dialog = Gtk.MessageDialog(None,
                             Gtk.DialogFlags.DESTROY_WITH_PARENT,
                             Gtk.MessageType.WARNING,
                             buttons,
                             text)
        return dialog

    def create_file_chooser_dialog(self, text, cls, name=Gtk.STOCK_OPEN):
        text = None
        dialog = Gtk.FileChooserDialog(
            text, cls,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, name, Gtk.ResponseType.OK)
            )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            text = dialog.get_filename()
        dialog.destroy()
        return text

    def create_checkbox(self, name):
        chk_btn = Gtk.CheckButton(name)
        return chk_btn

    def create_alignment(self, xalign=0, yalign=0, xscale=0, yscale=0):
        align = Gtk.Alignment()
        align.set(xalign, yalign, xscale, yscale)
        return align

