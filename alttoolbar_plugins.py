# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright (C) 2015 - fossfreedom
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

from gi.repository import Gtk
from gi.repository import Peas
from gi.repository import PeasGtk
from gi.repository import Gio
from gi.repository import Pango
from gi.repository import GLib

import rb
import webbrowser

class PluginListRow(Gtk.Box):
        
    def __init__(self, plugin, switch_callback):
        super(PluginListRow, self).__init__()
        
        self.plugin = plugin
        self._refresh = False
        
        self._switch_callback = switch_callback
        
        label1 = Gtk.Label()
        label1.set_markup("<b>" + plugin.get_name() + "</b>")
        label1.set_ellipsize(Pango.EllipsizeMode.END)
        label1.props.halign = Gtk.Align.START
        label2 = Gtk.Label(plugin.get_description())
        label2.set_ellipsize(Pango.EllipsizeMode.END)
        label2.props.halign = Gtk.Align.START
        
        switch = Gtk.Switch.new()
        self._switch = switch
        
        if not plugin.is_available():
            switch.set_sensitive(False)
            
        switch.set_active(plugin.is_loaded())
    
        switch.connect('notify::active', self._switch_changed)
        
        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.pack_start(label1, True, False, 0)
        box.pack_start(label2, True, False, 1)
        
        box1 = Gtk.Box()
        box1.set_orientation(Gtk.Orientation.VERTICAL)
        box1.pack_end(Gtk.Label(""), False, False, 0)
        box1.pack_end(switch, False, False, 1)
        box1.pack_end(Gtk.Label(""), False, False, 2)
        
        self.pack_start(box, False, False, 0)
        self.pack_end(box1, False, False, 1)
        
    def _switch_changed(self, switch, *args):
        if self._refresh:
            return False
            
        self._refresh = True
        
        def delay(*args):
            print ("switch_changed")
            print (switch.get_active())
            self._switch_callback(switch, self.plugin)
            
            self._refresh = False
            
        GLib.timeout_add(250, delay, None)
            
    def refresh(self, *args):
        self._switch.set_sensitive(self.plugin.is_available())
            
        if self._switch.get_active() == self.plugin.is_loaded():
            return
            
        self._switch.set_active(self.plugin.is_loaded())

class PluginDialog(Gtk.Dialog):
        
    def __init__(self, parent_window, has_headerbar):
        if has_headerbar:
            super(PluginDialog, self).__init__(use_header_bar=True, 
                                               parent=parent_window, 
                                               flags = Gtk.DialogFlags.MODAL)
        else:
            super(PluginDialog, self).__init__(parent=parent_window, 
                                               flags = Gtk.DialogFlags.MODAL)

        self._has_headerbar = has_headerbar
        self._parent_window = parent_window
        
        self.set_default_size(600, 400)

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
            
        #peas load-plugin and unload-plugin - should connect to these for engine load/unload.  This should update our listbox state
        
        toolbar = Gtk.Toolbar.new()
        context = toolbar.get_style_context()
        context.add_class(Gtk.STYLE_CLASS_INLINE_TOOLBAR)
        
        item = Gtk.ToolItem.new()
        minitoolbar_box = Gtk.Box()
        context = minitoolbar_box.get_style_context()
        context.add_class('linked')
        
        btn = Gtk.Button()
        icon = Gio.ThemedIcon(name="preferences-system-symbolic")
        image = Gtk.Image()
        btn.add(image)
        image.set_from_gicon(icon, Gtk.IconSize.BUTTON)
        minitoolbar_box.pack_start(btn, False, False, 0)
        btn.connect('clicked', self._preferences_button_clicked)
        self._preferences_button = btn
        
        btn = Gtk.Button()
        icon = Gio.ThemedIcon(name="dialog-information-symbolic")
        image = Gtk.Image()
        btn.add(image)
        image.set_from_gicon(icon, Gtk.IconSize.BUTTON)
        minitoolbar_box.pack_start(btn, False, False, 1)
        btn.connect('clicked', self._info_button_clicked)
        self._info_button = btn
        
        btn = Gtk.Button()
        icon = Gio.ThemedIcon(name="system-help-symbolic")
        image = Gtk.Image()
        btn.add(image)
        image.set_from_gicon(icon, Gtk.IconSize.BUTTON)
        minitoolbar_box.pack_start(btn, False, False, 2)
        btn.connect('clicked', self._help_button_clicked)
        self._help_button = btn
        
        item = Gtk.ToolItem.new()
        item.add(minitoolbar_box)
        toolbar.insert(item, 0)
        
        contentbox = Gtk.Box()
        contentbox.set_orientation(Gtk.Orientation.VERTICAL)
        
        scrollwindow = Gtk.ScrolledWindow.new(None, None)
        scrollwindow.add(listbox)
        scrollwindow.props.hexpand = True
        scrollwindow.props.vexpand = True
        
        contentbox.pack_start(scrollwindow, True, True, 0)
        contentbox.pack_start(toolbar, False, False, 1)
        
        self.props.title="Configure Plugins"
        
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
        print (module_name)
        
        if module_name in self._items:
            self._items[module_name].refresh()
            
    def _listbox_sort(self, row1, row2, *args):
        return row1.get_child().plugin.get_name().lower() > row2.get_child().plugin.get_name().lower()

    def _switch_callback(self, switch, plugin):
        value = switch.get_active()
        print (switch)
        print (plugin)
        
        if value and not plugin.is_loaded():
            self._peas.load_plugin(plugin)
        
        if not value and plugin.is_loaded():
            self._peas.unload_plugin(plugin)
        
    def _get_preference_widget(self, row):
        try:
            ext = self._peas.create_extension(row.get_child().plugin, PeasGtk.Configurable, None)
            widget = ext.create_configure_widget()
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
            
            help_link = row.get_child().plugin.get_help_uri()
            
            if help_link:
                self._help_button.set_sensitive(True)
            else:
                self._help_button.set_sensitive(False)
            
    def _help_button_clicked(self, *args):
        row = self._listbox.get_selected_row()
        help_link = row.get_child().plugin.get_help_uri()
        
        webbrowser.open(help_link)
        
    def _info_button_clicked(self, *args):
        if self._has_headerbar:
            dlg = Gtk.Dialog(use_header_bar=True, flags = Gtk.DialogFlags.MODAL)
            dlg.get_header_bar().set_show_close_button(True)
        else:
            dlg = Gtk.Dialog(flags = Gtk.DialogFlags.MODAL)
            dlg.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
            
        row = self._listbox.get_selected_row()
        
        title = row.get_child().plugin.get_name()
        version = row.get_child().plugin.get_version()
        if version:
            title = title + " " + version
        dlg.props.title = title
        
        area = dlg.get_content_area()
        
        widget = Gtk.Box()
        widget.set_orientation(Gtk.Orientation.VERTICAL)
        
        website = row.get_child().plugin.get_website()
        copyright = row.get_child().plugin.get_copyright()
        description = row.get_child().plugin.get_description()
        authors = row.get_child().plugin.get_authors()
        
        pos = 0
        
        def get_label(label):
            label = Gtk.Label(label)
            label.set_line_wrap(True)
            label.set_justify(Gtk.Justification.CENTER)
            return label
        
        if description:
            label = get_label(description)
            
            widget.pack_start(label, False, False, pos)
            pos += 1
            widget.pack_start(Gtk.Label(""), False, False, pos)
            pos += 1
            
        if copyright:
            label = get_label(copyright)
            widget.pack_start(label, False, False, pos)
            pos += 1
            widget.pack_start(Gtk.Label(""), False, False, pos)
            pos += 1
        
            
        #if authors:
        #    label = get_label(authors)
        #    widget.pack_start(label, False, False, pos)
        #    pos += 1
        #    widget.pack_start(Gtk.Label(""), False, False, pos)
        #    pos += 1
            
        if website:
            label = Gtk.Label()
            print ("<a href=\"" + website + "\">" + website + "</a>")
            label.set_markup("<a href=\"" + website + "\">" + website + "</a>")
            widget.pack_start(label, False, False, pos)
            pos += 1
            widget.pack_start(Gtk.Label(""), False, False, pos)
            pos += 1
        
        
        widget.show_all()
        frame = Gtk.Frame.new("")
        frame.props.margin = 8
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        frame.add(widget)
        frame.show_all()
        
        area.add(frame)
        dlg.set_default_size(400, 300)
        
        dlg.run()
        dlg.destroy()
        
    def _preferences_button_clicked(self, *args):
        row = self._listbox.get_selected_row()
        
        widget = self._get_preference_widget(row)
        
        if not widget:
            return
            
        if self._has_headerbar:
            dlg = Gtk.Dialog(use_header_bar=True, flags = Gtk.DialogFlags.MODAL)
            dlg.get_header_bar().set_show_close_button(True)
        else:
            dlg = Gtk.Dialog(flags = Gtk.DialogFlags.MODAL)
            dlg.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
            
        dlg.props.title = row.get_child().plugin.get_name()
        area = dlg.get_content_area()
        area.add(widget)
        dlg.run()
        dlg.destroy()
