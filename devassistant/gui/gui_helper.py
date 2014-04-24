#!/usr/bin/env python
import os
import re

from gi.repository import Gtk, Gdk
from textwrap import wrap

class GuiHelper(object):
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
    def create_box(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=0):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        hbox.set_homogeneous(False)
        return hbox

    def button_with_label(self, description, assistants=None, sensitive=True):
        btn = self.create_button()
        label = self.create_label(description)
        if assistants != None:
            hbox = self.create_box(orientation=Gtk.Orientation.VERTICAL)
            hbox.pack_start(label, False, False, 0)
            labelass = self.create_label(assistants, justify=Gtk.Justification.LEFT)
            labelass.set_alignment(0,0)
            hbox.pack_start(labelass,False, False, 12)
            btn.add(hbox)
        else:
            btn.add(label)
        return btn

    def create_image(self, image_name=None):
        image = Gtk.Image()
        image.set_from_file(image_name)
        return image

    def button_with_image(self, description, image=None, sensitive=True):
        btn = self.create_button()
        btn.set_sensitive(sensitive)
        hbox = self.create_box()
        img = self.create_image(image_name=image)
        hbox.pack_start(img, False, False, 12)
        label = self.create_label(description)
        hbox.pack_start(label, False, False, 0)
        btn.add(hbox)
        return btn

    def checkbutton_with_label(self, description):
        actBtn = Gtk.CheckButton(description)
        align = self.create_alignment()
        #align.add(actBtn)
        actBtn.add(align)
        return align

    def create_checkbutton(self, text=""):
        """
        This is generalized method for creating Gtk.CheckButton
        """
        btn = Gtk.CheckButton()
        return btn

    def create_checkbox(self, name, margin=10):
        chk_btn = Gtk.CheckButton(name)
        chk_btn.set_margin_right(margin)
        return chk_btn

    def create_entry(self, text="", sensitive="False"):
        textEntry = Gtk.Entry()
        textEntry.set_sensitive(sensitive)
        textEntry.set_text(text)
        return textEntry

    def create_link_button(self, text="None", uri="None"):
        linkbtn = Gtk.LinkButton(uri, text)
        return linkbtn;


    def create_button(self, style=Gtk.ReliefStyle.NORMAL):
        """
        This is generalized method for creating Gtk.Button
        """
        btn = Gtk.Button()
        btn.set_relief(style)
        return btn

    def create_menu_item(self, text):
        menu_item = Gtk.MenuItem(text)
        return menu_item

    def create_imagemenu_item(self, text, image_name):
        menu_item = Gtk.ImageMenuItem(text)
        img = self.create_image(image_name)
        menu_item.set_image(img)
        return menu_item

    def create_label(self, name, justify=Gtk.Justification.CENTER, wrap=True, tooltip=None):
        """
        The function is used for creating lable with HTML text
        """
        label = Gtk.Label()
        name = name.replace('|', '\n')
        label.set_markup(name)
        label.set_justify(justify)
        label.set_line_wrap(wrap)
        if tooltip is not None:
            label.set_has_tooltip(True)
            label.connect("query-tooltip", self.parent._tooltip_queries, tooltip)
        return label

    def add_button(self, grid_lang, ass, row, column):
        """
        The function is used for creating button with all features
        like signal on tooltip and signal on clicked
        The function does not have any menu.
        Button is add to the Gtk.Grid
        """
        #print "gui_helper add_button"
        image_name = ass[0].icon_path
        if not os.path.exists(image_name):
            btn = self.button_with_label("<b>"+ass[0].fullname+"</b>")
        else:
            btn = self.button_with_image("<b>"+ass[0].fullname+"</b>", image=ass[0].icon_path)
        #print "Dependencies button",ass[0]._dependencies
        if ass[0].description:
            btn.set_has_tooltip(True)
            btn.connect("query-tooltip",
                        self.parent._tooltip_queries,
                        self.get_formated_description(ass[0].description)
                        )
        btn.connect("clicked", self.parent.btn_clicked, ass[0].name)
        if row == 0 and column == 0:
            grid_lang.add(btn)
        else:
            grid_lang.attach(btn, column, row, 1, 1)
        return btn

    def create_menu(self):
        menu = Gtk.Menu()
        return menu

    def menu_item(self, assistant, subassistant, path):
        if not os.path.exists(subassistant[0].icon_path):
            menu_item = self.create_menu_item(subassistant[0].fullname)
        else:
            menu_item = self.create_imagemenu_item(subassistant[0].fullname, subassistant[0].icon_path)
        if subassistant[0].description:
            menu_item.set_has_tooltip(True)
            menu_item.connect("query-tooltip",
                              self.parent._tooltip_queries,
                              self.get_formated_description(subassistant[0].description),
                              )
        menu_item.connect("select", self.parent.submenu_select, path)
        menu_item.connect("button-press-event", self.parent.submenu_pressed)
        menu_item.show()
        return menu_item

    def generate_menu(self, ass, text, path=[], level=0):
        menu = self.create_menu()
        for index, sub in enumerate(sorted(ass[1], key=lambda y: y[0].fullname.lower())):
            if index != 0:
                text += "|"
            text += "- "+sub[0].fullname
            new_path = list(path)
            if level == 0:
                new_path.append(ass[0].name)
            new_path.append(sub[0].name)
            menu_item = self.menu_item(ass, sub, new_path)
            if sub[1]:
                # If assistant has subassistants
                (sub_menu, txt) = self.generate_menu(sub, text, new_path, level=level+1)
                menu_item.set_submenu(sub_menu)
            menu.append(menu_item)
        return menu, text

    def add_submenu(self, grid_lang, ass, row, column):
        """
        The function is used for creating button with menu and submenu.
        Also signal on tooltip and signal on clicked are specified
        Button is add to the Gtk.Grid
        """
        text = "Available subassistants:\n"
        # Generate menus
        (menu, text) = self.generate_menu(ass, text)
        menu.show_all()
        description = self.get_formated_description(ass[0].description)+"\n\n" if ass[0].description else ""
        description += text.replace('|', '\n')
        image_name = ass[0].icon_path
        lbl_text = "<b>"+ass[0].fullname+"</b>"
        if not os.path.exists(image_name):
            btn = self.button_with_label(lbl_text)
        else:
            btn = self.button_with_image(lbl_text, image=image_name)
        btn.set_has_tooltip(True)
        btn.connect("query-tooltip",
                    self.parent._tooltip_queries,
                    description
                    )
        btn.connect_object("event", self.parent.btn_press_event, menu)
        if row == 0 and column == 0:
            grid_lang.add(btn)
        else:
            grid_lang.attach(btn, column, row, 1, 1)

    def get_btn_label(self, btn):
        return btn.get_label()

    def get_btn_lower_label(self, btn):
        label = self.get_btn_label(btn)
        return label.lower()

    def get_btn_lower_replace(self, btn):
        label = self.get_btn_lower_label(btn)
        return label.replace("-", "_")

    def get_formated_description(self, description):
        return '\n'.join(wrap(description, 60))

    def create_scrolled_window(self, layout_manager, horizontal=Gtk.PolicyType.NEVER, vertical=Gtk.PolicyType.ALWAYS):
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(layout_manager)
        scrolled_window.set_policy(horizontal, vertical)
        return scrolled_window

    def create_gtk_grid(self, row_spacing=6, col_spacing=6, row_homogenous=False, col_homogenous=True):
        grid_lang = Gtk.Grid()
        grid_lang.set_column_spacing(row_spacing)
        grid_lang.set_row_spacing(col_spacing)
        grid_lang.set_border_width(12)
        grid_lang.set_row_homogeneous(row_homogenous)
        grid_lang.set_column_homogeneous(col_homogenous)
        return grid_lang

    def create_notebook(self, position=Gtk.PositionType.TOP):
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(position)
        notebook.set_show_border(True)
        return notebook

    def create_message_dialog(self, text, buttons=Gtk.ButtonsType.CLOSE, icon=Gtk.MessageType.WARNING):
        dialog = Gtk.MessageDialog(None,
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   icon,
                                   buttons,
                                   text
        )
        return dialog

    def create_question_dialog(self, text, second_text):
        dialog = self.create_message_dialog(text, buttons=Gtk.ButtonsType.YES_NO, icon=Gtk.MessageType.QUESTION)
        dialog.format_secondary_text(second_text)
        response = dialog.run()
        dialog.destroy()
        return response

    def execute_dialog(self, title):
        md = self.create_message_dialog(title)
        md.run()
        md.destroy()
        return

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

    def create_alignment(self, xalign=0, yalign=0, xscale=0, yscale=0):
        align = Gtk.Alignment()
        align.set(xalign, yalign, xscale, yscale)
        return align

    def create_textview(self, wrap=Gtk.WrapMode.WORD_CHAR, justify=Gtk.Justification.LEFT, visible=True, editable=True):
        text_view = Gtk.TextView()
        text_view.set_wrap_mode(wrap)
        text_view.set_editable(editable)
        if not editable:
            text_view.set_cursor_visible(False)
        else:
            text_view.set_cursor_visible(visible)
        text_view.set_justification(justify)
        return text_view

    def create_tree_view(self, model=None, mode=Gtk.SelectionMode.SINGLE):
        tree_view = Gtk.TreeView()
        if model != None:
            tree_view.set_model(model)
        return tree_view

    def create_cell_renderer_text(self, tree_view, title="title", assign=0, editable=False):
        renderer = Gtk.CellRendererText()
        renderer.set_property('editable', editable)
        column = Gtk.TreeViewColumn(title, renderer, text=assign)
        tree_view.append_column(column)

    def create_cell_renderer_combo(self, tree_view, title="title", assign=0, editable=False, model=None, function=None):
        renderer_combo = Gtk.CellRendererCombo()
        renderer_combo.set_property('editable', editable)
        if model:
            renderer_combo.set_property('model', model)
        if function:
            renderer_combo.connect("edited", function)
        renderer_combo.set_property("text-column", 0)
        renderer_combo.set_property("has-entry", False)
        column = Gtk.TreeViewColumn(title, renderer_combo, text=assign)
        tree_view.append_column(column)

    def create_clipboard(self, text, selection=Gdk.SELECTION_CLIPBOARD):
        clipboard = Gtk.Clipboard.get(selection)
        clipboard.set_text('\n'.join(text), -1)
        clipboard.store()
        return clipboard
