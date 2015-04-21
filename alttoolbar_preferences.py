# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright (C) 2014 - fossfreedom
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

# define plugin

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import PeasGtk
from gi.repository import Gio

import rb

class GSetting:
    '''
    This class manages the different settings that the plugin has to
    access to read or write.
    '''
    # storage for the instance reference
    __instance = None

    class __impl:
        """ Implementation of the singleton interface """
        # below public variables and methods that can be called for GSetting
        def __init__(self):
            '''
            Initializes the singleton interface, assigning all the constants
            used to access the plugin's settings.
            '''
            self.Path = self._enum(
                PLUGIN='org.gnome.rhythmbox.plugins.alternative_toolbar')

            self.PluginKey = self._enum(
                DISPLAY_TYPE='display-type',
                START_HIDDEN='start-hidden',
                SHOW_COMPACT='show-compact',
                PLAYING_LABEL='playing-label',
                VOLUME_CONTROL='volume-control',
                INLINE_LABEL='inline-label',
                COMPACT_PROGRESSBAR='compact-progressbar',
                ENHANCED_SIDEBAR='enhanced-sidebar',
                EXPANDERS='expanders'
            )

            self.setting = {}

        def get_setting(self, path):
            '''
            Return an instance of Gio.Settings pointing at the selected path.
            '''
            try:
                setting = self.setting[path]
            except:
                self.setting[path] = Gio.Settings.new(path)
                setting = self.setting[path]

            return setting

        def get_value(self, path, key):
            '''
            Return the value saved on key from the settings path.
            '''
            return self.get_setting(path)[key]

        def set_value(self, path, key, value):
            '''
            Set the passed value to key in the settings path.
            '''
            self.get_setting(path)[key] = value

        def _enum(self, **enums):
            '''
            Create an enumn.
            '''
            return type('Enum', (), enums)

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if GSetting.__instance is None:
            # Create and remember instance
            GSetting.__instance = GSetting.__impl()

        # Store instance reference as the only member in the handle
        self.__dict__['_GSetting__instance'] = GSetting.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)


class Preferences(GObject.Object, PeasGtk.Configurable):
    '''
    Preferences for the Plugins. It holds the settings for
    the plugin and also is the responsible of creating the preferences dialog.
    '''
    __gtype_name__ = 'AlternativeToolbarPreferences'
    object = GObject.property(type=GObject.Object)


    def __init__(self):
        '''
        Initialises the preferences, getting an instance of the settings saved
        by Gio.
        '''
        GObject.Object.__init__(self)
        self.gs = GSetting()
        self.plugin_settings = self.gs.get_setting(self.gs.Path.PLUGIN)

    def do_create_configure_widget(self):
        '''
        Creates the plugin's preferences dialog
        '''
        print("DEBUG - create_display_contents")
        # create the ui
        self._first_run = True

        builder = Gtk.Builder()
        builder.add_from_file(rb.find_plugin_file(self,
                                                  'ui/altpreferences.ui'))
        builder.connect_signals(self)

        # bind the toggles to the settings
        start_hidden = builder.get_object('start_hidden_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.START_HIDDEN,
                                  start_hidden, 'active', Gio.SettingsBindFlags.DEFAULT)

        show_compact = builder.get_object('show_compact_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.SHOW_COMPACT,
                                  show_compact, 'active', Gio.SettingsBindFlags.DEFAULT)

        self.display_type = self.plugin_settings[self.gs.PluginKey.DISPLAY_TYPE]
        self.auto_radiobutton = builder.get_object('auto_radiobutton')
        self.headerbar_radiobutton = builder.get_object('headerbar_radiobutton')
        self.toolbar_radiobutton = builder.get_object('toolbar_radiobutton')

        playing_label = builder.get_object('playing_label_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.PLAYING_LABEL,
                                  playing_label, 'active', Gio.SettingsBindFlags.DEFAULT)

        inline_label = builder.get_object('inline_label_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.INLINE_LABEL,
                                  inline_label, 'active', Gio.SettingsBindFlags.DEFAULT)

        volume_control = builder.get_object('volume_control_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.VOLUME_CONTROL,
                                  volume_control, 'active', Gio.SettingsBindFlags.DEFAULT)

        compact_control = builder.get_object('compact_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.COMPACT_PROGRESSBAR,
                                  compact_control, 'active', Gio.SettingsBindFlags.DEFAULT)

        enhanced_sidebar = builder.get_object('enhanced_sidebar_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.ENHANCED_SIDEBAR,
                                  enhanced_sidebar, 'active', Gio.SettingsBindFlags.DEFAULT)

        if self.display_type == 0:
            self.auto_radiobutton.set_active(True)
        elif self.display_type == 1:
            self.headerbar_radiobutton.set_active(True)
        else:
            self.toolbar_radiobutton.set_active(True)

        self._first_run = False

        return builder.get_object('preferences_box')

    def on_display_type_radiobutton_toggled(self, button):
        if self._first_run:
            return

        if button.get_active():
            if button == self.auto_radiobutton:
                self.plugin_settings[self.gs.PluginKey.DISPLAY_TYPE] = 0
            elif button == self.headerbar_radiobutton:
                self.plugin_settings[self.gs.PluginKey.DISPLAY_TYPE] = 1
            else:
                self.plugin_settings[self.gs.PluginKey.DISPLAY_TYPE] = 2

