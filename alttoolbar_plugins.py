# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright (C) 2015 - 2020 David Mohammed <fossfreedom@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import gettext
import re
import webbrowser

from alttoolbar_preferences import CoverLocale
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import Peas
from gi.repository import PeasGtk


class PluginListRow(Gtk.ListBoxRow):
    def __init__(self, plugin, switch_callback):
        super(PluginListRow, self).__init__()

        self.plugin = plugin
        self._refresh = False

        self._switch_callback = switch_callback

        label1 = Gtk.Label()
        escape = GLib.markup_escape_text(plugin.get_name())
        label1.set_markup("<b>" + escape + "</b>")
        label1.set_ellipsize(Pango.EllipsizeMode.END)
        label1.props.halign = Gtk.Align.START
        label1.set_has_tooltip(True)
        label1.props.margin_top = 5
        label1.connect('query-tooltip', self._display_tooltip)
        label2 = Gtk.Label(plugin.get_description())
        label2.set_ellipsize(Pango.EllipsizeMode.END)
        label2.props.halign = Gtk.Align.START
        label2.set_has_tooltip(True)
        label2.connect('query-tooltip', self._display_tooltip)
        label2.props.margin_bottom = 5

        switch = Gtk.Switch.new()
        self._switch = switch
        switch.props.valign = Gtk.Align.CENTER

        sensitive = False

        try:
            if plugin.is_available():
                sensitive = True
            switch.set_active(plugin.is_loaded())
        except:
            pass

        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.pack_start(label1, True, False, 0)
        box.pack_start(label2, True, False, 1)

        outerbox = Gtk.Box()
        outerbox.set_orientation(Gtk.Orientation.HORIZONTAL)
        outerbox.pack_start(Gtk.Label("  "), False, False, 0)
        outerbox.pack_start(box, False, False, 1)
        outerbox.pack_end(switch, False, False, 3)

        self.add(outerbox)
        self.outerbox = outerbox

        if not sensitive:
            self.add_error()

        switch.connect('notify::active', self._switch_changed)

    def _display_tooltip(self, label, x, y, mode, tooltip):
        if label.get_layout().is_ellipsized():
            tooltip.set_text(label.get_text())
            return True
        return False

    def _switch_changed(self, switch, *args):
        if self._refresh:
            return False

        self._refresh = True

        def delay(*args):
            print("switch_changed")
            print(switch.get_active())
            self._switch_callback(switch, self.plugin)

            self._refresh = False

        GLib.timeout_add(250, delay, None)

    def add_error(self):
        icon = Gio.ThemedIcon(name="dialog-error-symbolic")
        error_image = Gtk.Image()
        error_image.props.margin = 5
        error_image.set_from_gicon(icon, Gtk.IconSize.BUTTON)
        error_image.show_all()
        error_image.set_has_tooltip(True)
        error_image.set_tooltip_text(_('The plugin cannot be enabled'))
        self.outerbox.pack_end(error_image, False, False, 4)
        self.set_sensitive(False)

    def refresh(self, *args):
        try:

            if not self.plugin.is_available():
                self.add_error()

            if self._switch.get_active() == self.plugin.is_loaded():
                return

            self._switch.set_active(self.plugin.is_loaded())
        except:
            self.add_error()


class PluginDialog(Gtk.Dialog):
    def __init__(self, parent_window, has_headerbar):
        if has_headerbar:
            super(PluginDialog, self).__init__(use_header_bar=True,
                                               parent=parent_window,
                                               flags=Gtk.DialogFlags.MODAL)
        else:
            super(PluginDialog, self).__init__(parent=parent_window,
                                               flags=Gtk.DialogFlags.MODAL)

        self._has_headerbar = has_headerbar
        self._parent_window = parent_window

        listbox = Gtk.ListBox.new()
        listbox.set_sort_func(self._listbox_sort, None)
        self._listbox = listbox

        self._items = {}

        self._peas = Peas.Engine.get_default()
        plugins = self._peas.get_plugin_list()
        self._peas.connect_after('unload-plugin', self._on_load_unload_plugin)
        self._peas.connect_after('load-plugin', self._on_load_unload_plugin)

        for plugin in plugins:
            if not plugin.is_builtin() and not plugin.is_hidden():
                row = PluginListRow(plugin, self._switch_callback)
                self._items[plugin.get_module_name()] = row
                listbox.add(row)

        # locale stuff
        cl = CoverLocale()
        cl.switch_locale(cl.Locale.RB)

        def extract_text(str):
            # remove _ and (_A) type expressions
            translation = gettext.gettext(str)
            translation = re.sub('\(..\)', '', translation, flags=re.DOTALL)
            translation = translation.replace('_', '')
            return translation

        toolbar = Gtk.Toolbar.new()
        context = toolbar.get_style_context()
        context.add_class(Gtk.STYLE_CLASS_INLINE_TOOLBAR)

        item = Gtk.ToolItem.new()

        btn = Gtk.Button()
        icon = Gio.ThemedIcon(name="preferences-system-symbolic")
        image = Gtk.Image()
        image.props.margin = 3
        btn.add(image)
        btn.set_tooltip_text(extract_text("_Preferences"))
        image.set_from_gicon(icon, Gtk.IconSize.BUTTON)
        box = Gtk.Box()
        box.pack_start(btn, False, False, 0)
        item.add(box)
        toolbar.insert(item, 0)

        btn.connect('clicked', self._preferences_button_clicked)
        self._preferences_button = btn

        minitoolbar_box = Gtk.ButtonBox()
        context = minitoolbar_box.get_style_context()
        context.add_class('linked')
        minitoolbar_box.set_layout(Gtk.ButtonBoxStyle.START)

        btn = Gtk.Button()
        icon = Gio.ThemedIcon(name="preferences-system-details-symbolic")
        image = Gtk.Image()
        image.props.margin = 3
        btn.add(image)
        btn.set_tooltip_text(extract_text("_About"))
        image.set_from_gicon(icon, Gtk.IconSize.BUTTON)
        minitoolbar_box.add(btn)
        minitoolbar_box.child_set_property(btn, "non-homogeneous", True)
        btn.connect('clicked', self._info_button_clicked)
        self._info_button = btn

        btn = Gtk.Button()
        icon = Gio.ThemedIcon(name="help-contents-symbolic")
        image = Gtk.Image()
        image.props.margin = 3
        btn.add(image)
        btn.set_tooltip_text(extract_text("_Help"))
        image.set_from_gicon(icon, Gtk.IconSize.BUTTON)
        minitoolbar_box.add(btn)
        minitoolbar_box.child_set_property(btn, "non-homogeneous", True)
        btn.connect('clicked', self._help_button_clicked)
        self._help_button = btn

        item = Gtk.SeparatorToolItem.new()
        item.props.draw = False

        toolbar.insert(item, 1)
        toolbar.child_set_property(item, "expand", True)

        item = Gtk.ToolItem.new()
        item.add(minitoolbar_box)
        toolbar.insert(item, 2)

        contentbox = Gtk.Box()
        contentbox.set_orientation(Gtk.Orientation.VERTICAL)

        scrollwindow = Gtk.ScrolledWindow.new(None, None)
        scrollwindow.add(listbox)
        scrollwindow.props.hexpand = True
        scrollwindow.props.vexpand = True

        contentbox.pack_start(scrollwindow, True, True, 0)
        contentbox.pack_start(toolbar, False, False, 1)

        self.props.title = _("Configure Plugins")

        if not self._has_headerbar:
            self.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        else:
            headerbar = self.get_header_bar()
            headerbar.set_show_close_button(True)

        contentbox.show_all()

        area = self.get_content_area()
        area.add(contentbox)

        listbox.connect('row-selected', self._listbox_row_selected)

    def _on_load_unload_plugin(self, engine, plugin):
        module_name = plugin.get_module_name()
        print(module_name)

        if module_name in self._items:
            self._items[module_name].refresh()

    def _listbox_sort(self, row1, row2, *args):
        return row1.plugin.get_name().lower() > row2.plugin.get_name().lower()

    def _switch_callback(self, switch, plugin):
        value = switch.get_active()

        if value and not plugin.is_loaded():
            self._peas.load_plugin(plugin)

        if not value and plugin.is_loaded():
            self._peas.unload_plugin(plugin)

        row = switch.get_parent().get_parent()
        self._listbox.select_row(row)
        self._listbox_row_selected(_, row)

    def _get_preference_widget(self, row):
        try:
            ext = self._peas.create_extension(row.plugin,
                                              PeasGtk.Configurable,
                                              None)
            widget = ext.create_configure_widget()
            cl = CoverLocale()
            cl.switch_locale(cl.Locale.RB)
            return widget
        except:
            pass

        return None

    def _listbox_row_selected(self, listbox, row):
        if row:

            has_preference = False
            widget = self._get_preference_widget(row)
            if widget:
                has_preference = True

            self._preferences_button.set_sensitive(has_preference)

            help_link = row.plugin.get_help_uri()

            if help_link:
                self._help_button.set_sensitive(True)
            else:
                self._help_button.set_sensitive(False)

    def _help_button_clicked(self, *args):
        row = self._listbox.get_selected_row()
        help_link = row.plugin.get_help_uri()

        webbrowser.open(help_link)

    def _info_button_clicked(self, *args):
        if self._has_headerbar:
            dlg = Gtk.Dialog(use_header_bar=True, flags=Gtk.DialogFlags.MODAL)
            dlg.get_header_bar().set_show_close_button(True)
        else:
            dlg = Gtk.Dialog(flags=Gtk.DialogFlags.MODAL)
            dlg.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)

        row = self._listbox.get_selected_row()

        title = row.plugin.get_name()
        version = row.plugin.get_version()
        dlg.props.title = _("About this plugin")

        area = dlg.get_content_area()

        widget = Gtk.Box()
        widget.set_orientation(Gtk.Orientation.VERTICAL)

        website = row.plugin.get_website()
        copyright = row.plugin.get_copyright()
        description = row.plugin.get_description()
        # authors = row.plugin.get_authors()
        help = row.plugin.get_help_uri()

        pos = 0

        def get_label(label):
            label = Gtk.Label(label)
            label.set_line_wrap(True)
            label.set_justify(Gtk.Justification.CENTER)
            label.set_max_width_chars(60)
            return label

        label = Gtk.Label()
        escape = GLib.markup_escape_text(title)
        label.set_markup("<b>" + escape + "</b>")
        label.set_justify(Gtk.Justification.CENTER)
        label.props.margin_bottom = 5

        widget.pack_start(label, False, False, pos)
        pos += 1

        if version:
            label = get_label(_("Version: ") + version)
            label.props.margin_bottom = 5

            widget.pack_start(label, False, False, pos)
            pos += 1

        if description:
            label = get_label(description)
            label.props.margin_bottom = 5

            widget.pack_start(label, False, False, pos)
            pos += 1

        if copyright:
            label = get_label(copyright)
            label.props.margin_bottom = 5

            widget.pack_start(label, False, False, pos)
            pos += 1

        if title == _("Alternative Toolbar"):
            # special case for the this plugin
            grid = Gtk.Grid()
            grid.props.halign = Gtk.Align.CENTER

            label = Gtk.Label(_("Developer:"))
            label.props.halign = Gtk.Align.END

            grid.attach(label, 0, 0, 1, 1)

            link = Gtk.Label()
            link.props.halign = Gtk.Align.START
            m = " <a href=\"https://github.com/fossfreedom\">David " \
                "Mohammed</a>"
            link.set_markup(m)
            grid.attach(link, 1, 0, 1, 1)

            label = Gtk.Label(_("Designer:"))
            label.props.halign = Gtk.Align.END

            grid.attach(label, 0, 1, 1, 1)

            link = Gtk.Label()
            link.props.halign = Gtk.Align.START
            m = " <a href=\"https://github.com/me4oslav\">Georgi " \
                "Karavasilev</a>"
            link.set_markup(m)
            grid.attach(link, 1, 1, 1, 1)

            widget.pack_start(grid, False, False, pos)

            grid.props.margin_bottom = 5
            pos += 1

        box = Gtk.Box()
        box.set_homogeneous(True)

        def launch_browser(button, uri):
            webbrowser.open(uri)

        button = Gtk.Button(_("Help"))
        if help:
            button.connect('clicked', launch_browser, help)
        else:
            button.set_sensitive(False)

        box.pack_start(button, False, True, 0)

        button = Gtk.Button(_("Homepage"))
        if help:
            button.connect('clicked', launch_browser, website)
        else:
            button.set_sensitive(False)

        box.pack_start(Gtk.Label(""), False, True, 1)
        box.pack_start(Gtk.Label(""), False, True, 2)

        box.pack_start(button, False, True, 3)

        widget.pack_start(box, False, True, pos)
        # pos += 1

        widget.show_all()
        frame = Gtk.Frame.new("")
        frame.props.margin = 8
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.add(widget)
        frame.show_all()

        area.add(frame)
        dlg.set_resizable(False)

        dlg.run()
        dlg.destroy()

    def _preferences_button_clicked(self, *args):
        row = self._listbox.get_selected_row()

        widget = self._get_preference_widget(row)

        if not widget:
            return

        if self._has_headerbar:
            dlg = Gtk.Dialog(use_header_bar=True, flags=Gtk.DialogFlags.MODAL)
            dlg.get_header_bar().set_show_close_button(True)
        else:
            dlg = Gtk.Dialog(flags=Gtk.DialogFlags.MODAL)
            dlg.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)

        dlg.props.title = row.plugin.get_name()
        area = dlg.get_content_area()
        area.add(widget)
        dlg.set_resizable(False)
        dlg.run()
        dlg.destroy()
