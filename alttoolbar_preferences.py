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

# define plugin

import gettext
import locale
import os
import shutil
import sys

import gi
import rb
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import Gtk

gi.require_version('PeasGtk', '1.0')
from gi.repository import PeasGtk
from gi.repository import RB


class GSetting:
    """
    This class manages the different settings that the plugin has to
    access to read or write.
    """
    # storage for the instance reference
    __instance = None

    class __impl:
        """ Implementation of the singleton interface """

        # below public variables and methods that can be called for GSetting
        def __init__(self):
            """
            Initializes the singleton interface, assigning all the constants
            used to access the plugin's settings.
            """
            self.Path = self._enum(
                PLUGIN='org.gnome.rhythmbox.plugins.alternative_toolbar')

            self.PluginKey = self._enum(
                DISPLAY_TYPE='display-type',
                START_HIDDEN='start-hidden',
                SHOW_COMPACT='show-compact',
                PLAYING_LABEL='playing-label',
                VOLUME_CONTROL='volume-control',
                INLINE_LABEL='inline-label',
                ENHANCED_SIDEBAR='enhanced-sidebar',
                EXPANDERS='expanders',
                SHOW_TOOLTIPS='show-tooltips',
                ENHANCED_PLUGINS='enhanced-plugins',
                REPEAT_TYPE='repeat-type',
                SOURCE_TOOLBAR='show-source-toolbar',
                HORIZ_CATEGORIES='horiz-categories',
                APP_MENU='app-menu-display',
                DARK_THEME='dark-theme'
            )

            self.setting = {}

        def get_setting(self, path):
            """
            Return an instance of Gio.Settings pointing at the selected path.
            """
            try:
                setting = self.setting[path]
            except:
                self.setting[path] = Gio.Settings.new(path)
                setting = self.setting[path]

            return setting

        def get_value(self, path, key):
            """
            Return the value saved on key from the settings path.
            """
            return self.get_setting(path)[key]

        def set_value(self, path, key, value):
            """
            Set the passed value to key in the settings path.
            """
            self.get_setting(path)[key] = value

        def _enum(self, **enums):
            """
            Create an enumn.
            """
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


class CoverLocale:
    """
    This class manages the locale
    """
    # storage for the instance reference
    __instance = None

    class __impl:
        """ Implementation of the singleton interface """

        # below public variables and methods that can be called for CoverLocale
        def __init__(self):
            """
            Initializes the singleton interface, assigning all the constants
            used to access the plugin's settings.
            """
            self.Locale = self._enum(
                RB='rhythmbox',
                LOCALE_DOMAIN='alternative-toolbar')

        def switch_locale(self, locale_type):
            """
            Change the locale
            """
            locale.setlocale(locale.LC_ALL, '')
            locale.bindtextdomain(locale_type, RB.locale_dir())
            locale.textdomain(locale_type)
            gettext.bindtextdomain(locale_type, RB.locale_dir())
            gettext.textdomain(locale_type)
            gettext.install(locale_type)

        def get_locale(self):
            """
            return the string representation of the users locale
            for example
            en_US
            """
            return locale.getdefaultlocale()[0]

        def _enum(self, **enums):
            """
            Create an enumn.
            """
            return type('Enum', (), enums)

        def get_translation(self, value):
            """
            return the translated version of the string
            """
            return gettext.gettext(value)

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if CoverLocale.__instance is None:
            # Create and remember instance
            CoverLocale.__instance = CoverLocale.__impl()

        # Store instance reference as the only member in the handle
        self.__dict__['_CoverLocale__instance'] = CoverLocale.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)


class Preferences(GObject.Object, PeasGtk.Configurable):
    """
    Preferences for the Plugins. It holds the settings for
    the plugin and also is the responsible of creating the preferences dialog.
    """
    __gtype_name__ = 'AlternativeToolbarPreferences'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        """
        Initialises the preferences, getting an instance of the settings saved
        by Gio.
        """
        GObject.Object.__init__(self)
        self.gs = GSetting()
        self.plugin_settings = self.gs.get_setting(self.gs.Path.PLUGIN)

    def do_create_configure_widget(self):
        """
        Creates the plugin's preferences dialog
        """
        print("DEBUG - create_display_contents")
        # create the ui
        self._first_run = True

        cl = CoverLocale()
        cl.switch_locale(cl.Locale.LOCALE_DOMAIN)
        builder = Gtk.Builder()
        builder.set_translation_domain(cl.Locale.LOCALE_DOMAIN)
        builder.add_from_file(rb.find_plugin_file(self,
                                                  'ui/altpreferences.ui'))
        builder.connect_signals(self)

        # bind the toggles to the settings
        start_hidden = builder.get_object('start_hidden_checkbox')

        start_hidden.set_active(
            not self.plugin_settings[self.gs.PluginKey.START_HIDDEN])
        start_hidden.connect('toggled', self._start_hidden_checkbox_toggled)

        self._show_compact = builder.get_object('show_compact_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.SHOW_COMPACT,
                                  self._show_compact, 'active',
                                  Gio.SettingsBindFlags.DEFAULT)

        self._show_compact.connect('toggled',
                                   self._show_compact_checkbox_toggled)

        self._playing_label = builder.get_object('playing_label_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.PLAYING_LABEL,
                                  self._playing_label, 'active',
                                  Gio.SettingsBindFlags.DEFAULT)

        self._inline_label = builder.get_object('inline_label_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.INLINE_LABEL,
                                  self._inline_label, 'active',
                                  Gio.SettingsBindFlags.DEFAULT)

        volume_control = builder.get_object('volume_control_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.VOLUME_CONTROL,
                                  volume_control, 'active',
                                  Gio.SettingsBindFlags.DEFAULT)

        self._enhanced_sidebar = builder.get_object(
            'enhanced_sidebar_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.ENHANCED_SIDEBAR,
                                  self._enhanced_sidebar, 'active',
                                  Gio.SettingsBindFlags.DEFAULT)

        self._show_tooltips = builder.get_object('tooltips_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.SHOW_TOOLTIPS,
                                  self._show_tooltips, 'active',
                                  Gio.SettingsBindFlags.DEFAULT)

        self._enhanced_plugins = \
            builder.get_object('enhanced_plugins_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.ENHANCED_PLUGINS,
                                  self._enhanced_plugins, 'active',
                                  Gio.SettingsBindFlags.DEFAULT)

        self._dark_theme = \
            builder.get_object('dark_theme_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.DARK_THEME,
                                  self._dark_theme, 'active',
                                  Gio.SettingsBindFlags.DEFAULT)

        modern_switch = builder.get_object('modern_switch')
        # modern_switch.connect('state-set', self._modern_switch_state)
        modern_switch.connect('notify', self._modern_switch_state)

        # Determine what type of toolbar is to be displayed
        default = Gtk.Settings.get_default()
        display_type = self.plugin_settings[self.gs.PluginKey.DISPLAY_TYPE]

        if display_type == 0:
            if (not default.props.gtk_shell_shows_app_menu) or \
                    default.props.gtk_shell_shows_menubar:
                modern_switch.set_active(False)
            else:
                modern_switch.set_active(True)
        elif display_type == 1:
            modern_switch.set_active(True)
        else:
            modern_switch.set_active(False)

        if modern_switch.get_active():
            self._show_compact.set_active(True)

        self._show_compact_checkbox_toggled(self._show_compact)

        infobar = builder.get_object('infobar')
        button = infobar.add_button(_("Restart"), 1)
        # restart_button = builder.get_object('restart_button')
        button.connect('clicked', self._restart_button_clicked)

        self._hcategory_radiobutton = builder.get_object(
            'hcategory_radiobutton')
        self._vcategory_radiobutton = builder.get_object(
            'vcategory_radiobutton')

        category = self.plugin_settings[self.gs.PluginKey.HORIZ_CATEGORIES]
        if category:
            self._vcategory_radiobutton.set_active(True)
        else:
            self._hcategory_radiobutton.set_active(True)

        self._hcategory_radiobutton.connect('toggled',
                                            self._category_radiobutton)
        self._vcategory_radiobutton.connect('toggled',
                                            self._category_radiobutton)

        self._first_run = False

        return builder.get_object('preferences_box')

    def _category_radiobutton(self, button):
        if button.get_active():
            if button == self._hcategory_radiobutton:
                value = False
            else:
                value = True

            self.plugin_settings[self.gs.PluginKey.HORIZ_CATEGORIES] = value

    def _restart_button_clicked(self, *args):
        exepath = shutil.which('rhythmbox')
        os.execl(exepath, exepath, *sys.argv)

    def _start_hidden_checkbox_toggled(self, toggle_button):
        self.plugin_settings[self.gs.PluginKey.START_HIDDEN] = \
            not toggle_button.get_active()

    def _show_compact_checkbox_toggled(self, toggle_button):
        enabled = toggle_button.get_active()

        self._show_tooltips.set_sensitive(enabled)
        self._inline_label.set_sensitive(enabled)
        self._playing_label.set_sensitive(enabled)

    def _modern_switch_state(self, switch, param):
        state = switch.get_active()
        self._show_compact.set_sensitive(not state)

        if state:
            self._show_compact.set_active(True)
            self.plugin_settings[self.gs.PluginKey.DISPLAY_TYPE] = 1
        else:
            self.plugin_settings[self.gs.PluginKey.DISPLAY_TYPE] = 2
