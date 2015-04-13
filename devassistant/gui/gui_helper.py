#!/usr/bin/env python
"""
The module is used as wrap above Gtk and Gdk library
so that user can used already predefined functions
"""
import os

from gi.repository import Gtk, Gdk, GdkPixbuf
from textwrap import wrap


class GuiHelper(object):
    """
        The class is used for generating basic GUI widget
    """
    def __init__(self, parent):
        """
            This is general class for creating GUI
        """
        self.parent = parent

    def create_frame(self):
        """
            This function creates a frame
        """
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        return frame

    def create_box(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=0):
        """
            Function creates box. Based on orientation
            it can be either HORIZONTAL or VERTICAL
        """
        h_box = Gtk.Box(orientation=orientation, spacing=spacing)
        h_box.set_homogeneous(False)
        return h_box

    def button_with_label(self, description, assistants=None):
        """
            Function creates a button with lave.
            If assistant is specified then text is aligned
        """
        btn = self.create_button()
        label = self.create_label(description)
        if assistants is not None:
            h_box = self.create_box(orientation=Gtk.Orientation.VERTICAL)
            h_box.pack_start(label, False, False, 0)
            label_ass = self.create_label(
                assistants, justify=Gtk.Justification.LEFT
            )
            label_ass.set_alignment(0, 0)
            h_box.pack_start(label_ass, False, False, 12)
            btn.add(h_box)
        else:
            btn.add(label)
        return btn

    def create_image(self, image_name=None, scale_ratio=1, window=None):
        """
            The function creates a image from name defined in image_name
        """
        size = 48 * scale_ratio
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_name, -1, size, True)
        image = Gtk.Image()

        # Creating the cairo surface is necessary for proper scaling on HiDPI
        try:
            surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, scale_ratio, window)
            image.set_from_surface(surface)

        # Fallback for GTK+ older than 3.10
        except AttributeError:
            image.set_from_pixbuf(pixbuf)

        return image

    def button_with_image(self, description, image=None, sensitive=True):
        """
            The function creates a button with image
        """
        btn = self.create_button()
        btn.set_sensitive(sensitive)
        h_box = self.create_box()
        try:
            img = self.create_image(image_name=image,
                                    scale_ratio=btn.get_scale_factor(),
                                    window=btn.get_window())
        except: # Older GTK+ than 3.10
            img = self.create_image(image_name=image)
        h_box.pack_start(img, False, False, 12)
        label = self.create_label(description)
        h_box.pack_start(label, False, False, 0)
        btn.add(h_box)
        return btn

    def checkbutton_with_label(self, description):
        """
            The function creates a checkbutton with label
        """
        act_btn = Gtk.CheckButton(description)
        align = self.create_alignment()
        act_btn.add(align)
        return align

    def create_checkbutton(self):
        """
            This is generalized method for creating Gtk.CheckButton
        """
        btn = Gtk.CheckButton()
        return btn

    def create_checkbox(self, name, margin=10):
        """
        Function creates a checkbox with his name
        """
        chk_btn = Gtk.CheckButton(name)
        chk_btn.set_margin_right(margin)
        return chk_btn

    def create_entry(self, text="", sensitive="False"):
        """
        Function creates an Entry with corresponding text
        """
        text_entry = Gtk.Entry()
        text_entry.set_sensitive(sensitive)
        text_entry.set_text(text)
        return text_entry

    def create_link_button(self, text="None", uri="None"):
        """
        Function creates a link button with corresponding text and
        URI reference
        """
        link_btn = Gtk.LinkButton(uri, text)
        return link_btn

    def create_button(self, style=Gtk.ReliefStyle.NORMAL):
        """
        This is generalized method for creating Gtk.Button
        """
        btn = Gtk.Button()
        btn.set_relief(style)
        return btn

    def create_menu_item(self, text):
        """
        Function creates a menu item
        """
        menu_item = Gtk.MenuItem(text)
        return menu_item

    def create_image_menu_item(self, text, image_name):
        """
        Function creates a menu item with an image
        """
        menu_item = Gtk.ImageMenuItem(text)
        img = self.create_image(image_name)
        menu_item.set_image(img)
        return menu_item

    def create_label(self, name, justify=Gtk.Justification.CENTER, wrap_mode=True, tooltip=None):
        """
        The function is used for creating lable with HTML text
        """
        label = Gtk.Label()
        name = name.replace('|', '\n')
        label.set_markup(name)
        label.set_justify(justify)
        label.set_line_wrap(wrap_mode)
        if tooltip is not None:
            label.set_has_tooltip(True)
            label.connect("query-tooltip", self.parent.tooltip_queries, tooltip)
        return label

    def add_button(self, grid_lang, ass, row, column):
        """
        The function is used for creating button with all features
        like signal on tooltip and signal on clicked
        The function does not have any menu.
        Button is add to the Gtk.Grid on specific row and column
        """
        #print "gui_helper add_button"
        image_name = ass[0].icon_path
        label = "<b>" + ass[0].fullname + "</b>"
        if not image_name:
            btn = self.button_with_label(label)
        else:
            btn = self.button_with_image(label, image=ass[0].icon_path)
        #print "Dependencies button",ass[0]._dependencies
        if ass[0].description:
            btn.set_has_tooltip(True)
            btn.connect("query-tooltip",
                        self.parent.tooltip_queries,
                        self.get_formatted_description(ass[0].description)
            )
        btn.connect("clicked", self.parent.btn_clicked, ass[0].name)
        if row == 0 and column == 0:
            grid_lang.add(btn)
        else:
            grid_lang.attach(btn, column, row, 1, 1)
        return btn

    def add_install_button(self, grid_lang, row, column):
        """
        Add button that opens the window for installing more assistants
        """
        btn = self.button_with_label('<b>Install more...</b>')
        if row == 0 and column == 0:
            grid_lang.add(btn)
        else:
            grid_lang.attach(btn, column, row, 1, 1)
        btn.connect("clicked", self.parent.install_btn_clicked)
        return btn


    def create_menu(self):
        """
        The function creates a menu
        """
        menu = Gtk.Menu()
        return menu

    def menu_item(self, sub_assistant, path):
        """
        The function creates a menu item
        and assigns signal like select and button-press-event for
        manipulation with menu_item. sub_assistant and path
        """
        if not sub_assistant[0].icon_path:
            menu_item = self.create_menu_item(sub_assistant[0].fullname)
        else:
            menu_item = self.create_image_menu_item(
                sub_assistant[0].fullname, sub_assistant[0].icon_path
            )
        if sub_assistant[0].description:
            menu_item.set_has_tooltip(True)
            menu_item.connect("query-tooltip",
                              self.parent.tooltip_queries,
                              self.get_formatted_description(sub_assistant[0].description),
            )
        menu_item.connect("select", self.parent.sub_menu_select, path)
        menu_item.connect("button-press-event", self.parent.sub_menu_pressed)
        menu_item.show()
        return menu_item

    def generate_menu(self, ass, text, path=None, level=0):
        """
        Function generates menu from based on ass parameter
        """
        menu = self.create_menu()
        for index, sub in enumerate(sorted(ass[1], key=lambda y: y[0].fullname.lower())):
            if index != 0:
                text += "|"
            text += "- " + sub[0].fullname
            new_path = list(path)
            if level == 0:
                new_path.append(ass[0].name)
            new_path.append(sub[0].name)
            menu_item = self.menu_item(sub, new_path)
            if sub[1]:
                # If assistant has subassistants
                (sub_menu, txt) = self.generate_menu(sub, text, new_path, level=level + 1)
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
        path = []
        (menu, text) = self.generate_menu(ass, text, path=path)
        menu.show_all()
        if ass[0].description:
            description = self.get_formatted_description(ass[0].description) + "\n\n"
        else:
            description = ""
        description += text.replace('|', '\n')
        image_name = ass[0].icon_path
        lbl_text = "<b>" + ass[0].fullname + "</b>"
        if not image_name:
            btn = self.button_with_label(lbl_text)
        else:
            btn = self.button_with_image(lbl_text, image=image_name)
        btn.set_has_tooltip(True)
        btn.connect("query-tooltip",
                    self.parent.tooltip_queries,
                    description
        )
        btn.connect_object("event", self.parent.btn_press_event, menu)
        if row == 0 and column == 0:
            grid_lang.add(btn)
        else:
            grid_lang.attach(btn, column, row, 1, 1)

    def get_btn_label(self, btn):
        """
        Function returns button label
        """
        return btn.get_label()

    def get_btn_lower_label(self, btn):
        """
        Function returns button label on lower case format
        """
        label = self.get_btn_label(btn)
        return label.lower()

    def get_btn_lower_replace(self, btn):
        """
        Function returns button label with lower case format
        and char - is replaced with _
        """
        label = self.get_btn_lower_label(btn)
        return label.replace("-", "_")

    def get_formatted_description(self, description):
        """
        Function wraps text to 60 character
        """
        return '\n'.join(wrap(description, 60))

    def create_scrolled_window(self, layout_manager, horizontal=Gtk.PolicyType.NEVER, vertical=Gtk.PolicyType.ALWAYS):
        """
        Function creates a scrolled window with layout manager
        """
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(layout_manager)
        scrolled_window.set_policy(horizontal, vertical)
        return scrolled_window

    def create_gtk_grid(self, row_spacing=6, col_spacing=6, row_homogenous=False, col_homogenous=True):
        """
        Function creates a Gtk Grid with spacing
        and homogeous tags
        """
        grid_lang = Gtk.Grid()
        grid_lang.set_column_spacing(row_spacing)
        grid_lang.set_row_spacing(col_spacing)
        grid_lang.set_border_width(12)
        grid_lang.set_row_homogeneous(row_homogenous)
        grid_lang.set_column_homogeneous(col_homogenous)
        return grid_lang

    def create_notebook(self, position=Gtk.PositionType.TOP):
        """
        Function creates a notebook
        """
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(position)
        notebook.set_show_border(True)
        return notebook

    def create_message_dialog(self, text, buttons=Gtk.ButtonsType.CLOSE, icon=Gtk.MessageType.WARNING):
        """
        Function creates a message dialog with text
        and relevant buttons
        """
        dialog = Gtk.MessageDialog(None,
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   icon,
                                   buttons,
                                   text
        )
        return dialog

    def create_question_dialog(self, text, second_text):
        """
        Function creates a question dialog with title text
        and second_text
        """
        dialog = self.create_message_dialog(
            text, buttons=Gtk.ButtonsType.YES_NO, icon=Gtk.MessageType.QUESTION
        )
        dialog.format_secondary_text(second_text)
        response = dialog.run()
        dialog.destroy()
        return response

    def execute_dialog(self, title):
        """
        Function executes a dialog
        """
        msg_dlg = self.create_message_dialog(title)
        msg_dlg.run()
        msg_dlg.destroy()
        return

    def create_file_chooser_dialog(self, text, parent, name=Gtk.STOCK_OPEN):
        """
        Function creates a file chooser dialog with title text
        """
        text = None
        dialog = Gtk.FileChooserDialog(
            text, parent,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, name, Gtk.ResponseType.OK)
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            text = dialog.get_filename()
        dialog.destroy()
        return text

    def create_alignment(self, x_align=0, y_align=0, x_scale=0, y_scale=0):
        """
        Function creates an alignment
        """
        align = Gtk.Alignment()
        align.set(x_align, y_align, x_scale, y_scale)
        return align

    def create_textview(self, wrap_mode=Gtk.WrapMode.WORD_CHAR, justify=Gtk.Justification.LEFT, visible=True, editable=True):
        """
        Function creates a text view with wrap_mode
        and justification
        """
        text_view = Gtk.TextView()
        text_view.set_wrap_mode(wrap_mode)
        text_view.set_editable(editable)
        if not editable:
            text_view.set_cursor_visible(False)
        else:
            text_view.set_cursor_visible(visible)
        text_view.set_justification(justify)
        return text_view

    def create_tree_view(self, model=None):
        """
        Function creates a tree_view with model
        """
        tree_view = Gtk.TreeView()
        if model is not None:
            tree_view.set_model(model)
        return tree_view

    def create_cell_renderer_text(self, tree_view, title="title", assign=0, editable=False):
        """
        Function creates a CellRendererText with title
        """
        renderer = Gtk.CellRendererText()
        renderer.set_property('editable', editable)
        column = Gtk.TreeViewColumn(title, renderer, text=assign)
        tree_view.append_column(column)

    def create_cell_renderer_combo(self, tree_view, title="title", assign=0, editable=False, model=None, function=None):
        """'
        Function creates a CellRendererCombo with title, model
        """
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
        """
        Function creates a clipboard
        """
        clipboard = Gtk.Clipboard.get(selection)
        clipboard.set_text('\n'.join(text), -1)
        clipboard.store()
        return clipboard
