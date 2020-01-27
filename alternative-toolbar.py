# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright (C) 2015 - 2020 - David Mohammed <fossfreedom@ubuntu.com>
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

import gi
import rb
import os
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import Gtk

gi.require_version('Peas', '1.0')
from gi.repository import Peas
from gi.repository import RB

from alttoolbar_plugins import PluginDialog
from alttoolbar_preferences import CoverLocale
from alttoolbar_preferences import GSetting
from alttoolbar_preferences import Preferences
from alttoolbar_rb3compat import ActionGroup
from alttoolbar_rb3compat import ApplicationShell
from alttoolbar_rb3compat import gtk_version
from alttoolbar_type import AltToolbarCompact
from alttoolbar_type import AltToolbarHeaderBar
from alttoolbar_type import AltToolbarStandard

view_menu_ui = """
<ui>
  <menubar name="MenuBar">
    <menu name="ViewMenu" action="View">
        <menuitem name="Show Toolbar" action="ToggleToolbar" />
        <menuitem name="Show Source Toolbar"
        action="ToggleSourceMediaToolbar" />
    </menu>
  </menubar>
</ui>
"""

view_seek_menu_ui = """
<ui>
  <menubar name="MenuBar">
    <menu name="ViewMenu" action="View">
        <menuitem name="SeekBackward" action="SeekBackward" />
        <menuitem name="SeekForward" action="SeekForward" />
    </menu>
  </menubar>
</ui>
"""

seek_backward_time = 5
seek_forward_time = 10


class AltToolbarPlugin(GObject.Object, Peas.Activatable):
    """
    Main class of the plugin. Manages the activation and deactivation of the
    plugin.
    """
    __gtype_name = 'AltToolbarPlugin'
    object = GObject.property(type=GObject.Object)
    display_page_tree_visible = GObject.property(type=bool, default=False)
    show_album_art = GObject.property(type=bool, default=False)
    show_song_position_slider = GObject.property(type=bool, default=False)
    playing_label = GObject.property(type=bool, default=False)

    # signals
    # toolbar-visibility - bool parameter True = visible, False = not visible
    __gsignals__ = {
        'toolbar-visibility': (GObject.SIGNAL_RUN_LAST, None, (bool,))
    }

    def __init__(self):
        """
        Initialises the plugin object.
        """
        GObject.Object.__init__(self)
        self.appshell = None
        self.sh_psc = self.sh_op = self.sh_pc = None

    def do_activate(self):
        """
        Called by Rhythmbox when the plugin is activated. It creates the
        plugin's source and connects signals to manage the plugin's
        preferences.
        """

        self.shell = self.object
        self.db = self.shell.props.db
        self.shell_player = self.shell.props.shell_player

        # Prepare internal variables
        self.song_duration = 0
        self.entry = None
        self._plugin_dialog_width = 760
        self._plugin_dialog_height = 550

        # locale stuff
        cl = CoverLocale()
        cl.switch_locale(cl.Locale.LOCALE_DOMAIN)

        # for custom icons ensure we start looking in the plugin img folder
        # as a fallback
        theme = Gtk.IconTheme.get_default()
        theme.append_search_path(rb.find_plugin_file(self, 'img'))

        # Find the Rhythmbox Toolbar
        self.rb_toolbar = AltToolbarPlugin.find(self.shell.props.window,
                                                'main-toolbar', 'by_id')

        # get values from gsettings
        self.gs = GSetting()
        self.plugin_settings = self.gs.get_setting(self.gs.Path.PLUGIN)

        display_type = self.plugin_settings[self.gs.PluginKey.DISPLAY_TYPE]
        self.volume_control = self.plugin_settings[
            self.gs.PluginKey.VOLUME_CONTROL]
        self.show_compact_toolbar = self.plugin_settings[
            self.gs.PluginKey.SHOW_COMPACT]
        self.start_hidden = self.plugin_settings[
            self.gs.PluginKey.START_HIDDEN]
        self.inline_label = self.plugin_settings[
            self.gs.PluginKey.INLINE_LABEL]
        self.enhanced_sidebar = self.plugin_settings[
            self.gs.PluginKey.ENHANCED_SIDEBAR]
        self.show_tooltips = self.plugin_settings[
            self.gs.PluginKey.SHOW_TOOLTIPS]
        self.enhanced_plugins = self.plugin_settings[
            self.gs.PluginKey.ENHANCED_PLUGINS]
        self.horiz_categories = self.plugin_settings[
            self.gs.PluginKey.HORIZ_CATEGORIES]
        self.app_menu = self.plugin_settings[
            self.gs.PluginKey.APP_MENU]
        self.prefer_dark_theme = \
            self.plugin_settings[self.gs.PluginKey.DARK_THEME]

        # Add the various application view menus
        self.appshell = ApplicationShell(self.shell)
        self._add_menu_options()

        # Determine what type of toolbar is to be displayed
        if display_type == 0:
            if 'gnome' in os.environ['XDG_CURRENT_DESKTOP'].lower():
                display_type = 1
            else:
                display_type = 2

            self.plugin_settings[self.gs.PluginKey.DISPLAY_TYPE] = display_type

        self.toolbar_type = None
        if display_type == 1:
            self.toolbar_type = AltToolbarHeaderBar()
        elif self.show_compact_toolbar:
            self.toolbar_type = AltToolbarCompact()
        else:
            self.toolbar_type = AltToolbarStandard()

        self.toolbar_type.initialise(self)
        self.toolbar_type.post_initialise()

        try:
            process = Gio.Subprocess.new(['rhythmbox', '--version'],
                Gio.SubprocessFlags.STDOUT_PIPE)
            passval, buf, err = process.communicate_utf8(None)

            if passval:
                buf = buf[:-1]
                ver = buf.split(' ')[1]
        except:
            ver = "999.99.99"

        if self.enhanced_plugins and ver <= "3.4.3":
            # redirect plugins action to our implementation
            # after v3.4.3 plugins has been moved into
            # preferences so no need to activate our own
            # implementation

            action = Gio.SimpleAction.new('plugins', None)
            action.connect('activate', self._display_plugins)
            self.shell.props.application.add_action(action)

        self._connect_signals()
        self._connect_properties()

        # allow other plugins access to this toolbar
        self.shell.alternative_toolbar = self

        cl.switch_locale(cl.Locale.RB)

    def _display_plugins(self, *args):
        """
          display our implementation of the LibPeas Plugin window
        """

        has_headerbar = isinstance(self.toolbar_type, AltToolbarHeaderBar)

        if gtk_version() < 3.12:
            has_headerbar = False

        dlg = PluginDialog(self.shell.props.window, has_headerbar)
        response = 0
        dlg.set_default_size(self._plugin_dialog_width,
                             self._plugin_dialog_height)

        while response >= 0:
            response = dlg.run()
            print(response)

        self._plugin_dialog_width, self._plugin_dialog_height = dlg.get_size()
        dlg.destroy()

    def on_search(self, *args):
        self.toolbar_type.on_search_toggle()

    def _add_menu_options(self):
        """
          add the various menu options to the application
        """
        self.search_action_group = ActionGroup(self.shell,
                                             'AltToolbarPluginSearchActions')
        self.search_action_group.add_action(func=self.on_search,
                                          action_name='Search',
                                          label=_("Search"),
                                          action_type='app', accel="<Ctrl>f",
                                          tooltip=_(
                                              "Search"))
        self.appshell.insert_action_group(self.search_action_group)

        self.seek_action_group = ActionGroup(self.shell,
                                             'AltToolbarPluginSeekActions')
        self.seek_action_group.add_action(func=self.on_skip_backward,
                                          action_name='SeekBackward',
                                          label=_("Seek Backward"),
                                          action_type='app', accel="<Alt>Left",
                                          tooltip=_(
                                              "Seek backward, in current "
                                              "track, by 5 seconds."))
        self.seek_action_group.add_action(func=self.on_skip_forward,
                                          action_name='SeekForward',
                                          label=_("Seek Forward"),
                                          action_type='app',
                                          accel="<Alt>Right",
                                          tooltip=_(
                                              "Seek forward, in current "
                                              "track, by 10 seconds."))

        self.appshell.insert_action_group(self.seek_action_group)
        self.appshell.add_app_menuitems(view_seek_menu_ui,
                                        'AltToolbarPluginSeekActions', 'view')

        self.toggle_action_group = ActionGroup(self.shell,
                                               'AltToolbarPluginActions')
        self.toggle_action_group.add_action(func=self.toggle_visibility,
                                            action_name='ToggleToolbar',
                                            label=_(
                                                "Show Play-Controls Toolbar"),
                                            action_state=ActionGroup.TOGGLE,
                                            action_type='app',
                                            tooltip=_(
                                                "Show or hide the "
                                                "play-controls toolbar"))
        self.toggle_action_group.add_action(
            func=self.toggle_sourcemedia_visibility,
            action_name='ToggleSourceMediaToolbar',
            label=_("Show Source Toolbar"),
            action_state=ActionGroup.TOGGLE,
            action_type='app', accel="<Ctrl>t",
            tooltip=_("Show or hide the source toolbar"))

        self.appshell.insert_action_group(self.toggle_action_group)
        self.appshell.add_app_menuitems(view_menu_ui,
                                        'AltToolbarPluginActions', 'view')

    def _connect_properties(self):
        """
          bind plugin properties to various gsettings that we dynamically
          interact with
        """
        self.plugin_settings.bind(self.gs.PluginKey.PLAYING_LABEL, self,
                                  'playing_label',
                                  Gio.SettingsBindFlags.GET)

    def _connect_signals(self):
        """
          connect to various rhythmbox signals that the toolbars need
        """
        self.sh_display_page_tree = self.shell.props.display_page_tree.connect(
            "selected", self.on_page_change
        )

        self.sh_psc = self.shell_player.connect("playing-song-changed",
                                                self._sh_on_song_change)

        self.sh_op = self.shell_player.connect("elapsed-changed",
                                               self._sh_on_playing)

        self.sh_pc = self.shell_player.connect("playing-changed",
                                               self._sh_on_playing_change)

        self.sh_pspc = self.shell_player.connect(
            "playing-song-property-changed",
            self._sh_on_song_property_changed)

        self.rb_settings = Gio.Settings.new('org.gnome.rhythmbox')

        self.rb_settings.bind('show-album-art', self, 'show_album_art',
                              Gio.SettingsBindFlags.GET)
        self.connect('notify::show-album-art',
                     self.show_album_art_settings_changed)
        self.show_album_art_settings_changed(None)

        self.rb_settings.bind('show-song-position-slider', self,
                              'show_song_position_slider',
                              Gio.SettingsBindFlags.GET)
        self.connect('notify::show-song-position-slider',
                     self.show_song_position_slider_settings_changed)
        self.show_song_position_slider_settings_changed(None)

    def _sh_on_song_property_changed(self, sp, uri, property, old, new):
        """
           shell-player "playing-song-property-changed" signal handler
        """
        if sp.get_playing() and property in \
                ('artist',
                 'album',
                 'title',
                 RB.RHYTHMDB_PROP_STREAM_SONG_ARTIST,
                 RB.RHYTHMDB_PROP_STREAM_SONG_ALBUM,
                 RB.RHYTHMDB_PROP_STREAM_SONG_TITLE):
            entry = sp.get_playing_entry()
            self.toolbar_type.display_song(entry)

    def _sh_on_playing_change(self, player, playing):
        """
        Shell-player 'playing-change' signal handler.
        """
        self.toolbar_type.play_control_change(player, playing)
        if (self.song_duration != 0):
            self.toolbar_type.enable_slider(True)
        else:
            self.toolbar_type.enable_slider(False)
            if (hasattr(self.toolbar_type, "total_time_label")):
                label = ""
                self.toolbar_type.total_time_label.set_markup(label)

    def _sh_on_song_change(self, player, entry):
        """
        Shell-player 'playing-song-changed' signal handler.
        """
        if (entry is not None):
            self.song_duration = entry.get_ulong(RB.RhythmDBPropType.DURATION)
        else:
            self.song_duration = 0

        if hasattr(self.toolbar_type, 'song_progress'):
            self.toolbar_type.song_progress.adjustment.set_upper(
                self.song_duration or 1)
        self.toolbar_type.display_song(entry)

    def _sh_on_playing(self, player, seconds):
        """
        Shell-player 'elapsed-changed' signal handler.
        """
        if self.song_duration == 0:
            return
        try:
            slider = self.toolbar_type.song_progress
        except AttributeError:
            return
        with slider.handler_block(slider.changed_callback_id):
            slider.adjustment.set_value(seconds)

        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        total_minutes, total_seconds = divmod(self.song_duration, 60)
        total_hours, total_minutes = divmod(total_minutes, 60)

        if total_hours:
            label = "<small>{}:{:02}:{:02} / {}:{:02}:{:02}</small>".format(
                hours, minutes, seconds,
                total_hours, total_minutes, total_seconds)
        else:
            label = "<small>{:02}:{:02} / {:02}:{:02}</small>".format(
                minutes, seconds, total_minutes, total_seconds)
        self.toolbar_type.total_time_label.set_markup(label)

    def on_skip_backward(self, *args):
        """
           keyboard seek backwards signal handler
        """
        sp = self.object.props.shell_player
        if (sp.get_playing()[1]):
            seek_time = sp.get_playing_time()[1] - seek_backward_time
            print(seek_time)
            if (seek_time < 0):
                seek_time = 0

            print(seek_time)
            sp.set_playing_time(seek_time)

    def on_skip_forward(self, *args):
        """
           keyboard seek forwards signal handler
        """
        sp = self.object.props.shell_player
        if (sp.get_playing()[1]):
            seek_time = sp.get_playing_time()[1] + seek_forward_time
            song_duration = sp.get_playing_song_duration()
            if (song_duration > 0):  # sanity check
                if (seek_time > song_duration):
                    seek_time = song_duration

                sp.set_playing_time(seek_time)

    def show_song_position_slider_settings_changed(self, *args):
        """
           rhythmbox show-slider signal handler
        """
        self.toolbar_type.show_slider(self.show_song_position_slider)

    def show_album_art_settings_changed(self, *args):
        """
           rhythmbox show-album-art signal handler
        """
        self.toolbar_type.show_cover(self.show_album_art)

    def on_page_change(self, display_page_tree, page):
        """
           sources display-tree signal handler
        """
        print("page changed", page)
        self.toolbar_type.reset_categories_pos(page)
        self.toolbar_type.reset_toolbar(page)
        self.toolbar_type.reset_entryview(page)

    @staticmethod
    def find(node, search_id, search_type, button_label=None):
        """
        find various GTK Widgets
        :param node: node is the starting container to find from
        :param search_id: search_id is the GtkWidget type string or
        GtkWidget name
        :param search_type: search_type is the type of search
                            "by_name" to search by the type of GtkWidget
                            e.g. GtkButton
                            "by_id" to search by the GtkWidget (glade name)
                            e.g. box_1
        :param button_label: button_label to find specific buttons where we
        cannot use by_id
        :return:N/A
        """

        # Couldn't find better way to find widgets than loop through them
        # print("by_name %s by_id %s" % (node.get_name(),
        # Gtk.Buildable.get_name(node)))

        def extract_label(button):
            label = button.get_label()
            if label:
                return label

            child = button.get_child()
            if child and child.get_name() == "GtkLabel":
                return child.get_text()

            return None

        if isinstance(node, Gtk.Buildable):
            if search_type == 'by_id':
                if Gtk.Buildable.get_name(node) == search_id:
                    if button_label is None or (
                            'Button' in node.get_name() and extract_label(
                            node) == button_label):
                        return node
            elif search_type == 'by_name':
                if node.get_name() == search_id:
                    if button_label is None or (
                            'Button' in node.get_name() and extract_label(
                            node) == button_label):
                        return node

        if isinstance(node, Gtk.Container):
            for child in node.get_children():
                ret = AltToolbarPlugin.find(child, search_id, search_type,
                                            button_label)
                if ret:
                    return ret

        return None

    def do_deactivate(self):
        """
        Called by Rhythmbox when the plugin is deactivated. It makes sure to
        free all the resources used by the plugin.
        """
        del self.db

        if self.sh_op:
            self.shell_player.disconnect(self.sh_op)
            self.shell_player.disconnect(self.sh_psc)
            self.shell_player.disconnect(self.sh_pc)
            self.shell_player.disconnect(self.sh_pspc)
            # self.disconnect(self.sh_display_page)
            self.shell.props.display_page_tree.disconnect(
                self.sh_display_page_tree)
            del self.shell_player

        if self.appshell:
            self.appshell.cleanup()

        self.rb_toolbar.set_visible(True)

        self.toolbar_type.cleanup()

        del self.shell

    def toggle_visibility(self, action, param=None, data=None):
        """
        Display or Hide PlayControls signal handler
        :param action:
        :param param:
        :param data:
        :return:
        """
        action = self.toggle_action_group.get_action('ToggleToolbar')

        self.toolbar_type.set_visible(action.get_active())

    def toggle_sourcemedia_visibility(self, action, param=None, data=None):
        """
        Display or Hide the source toolbar
        :param action:
        :param param:
        :param data:
        :return:
        """
        action = self.toggle_action_group.get_action(
            'ToggleSourceMediaToolbar')

        self.toolbar_type.source_toolbar_visibility(action.get_active())

    def _translation_helper(self):
        """
        a method just to help out with translation strings
        it is not meant to be called by itself
        """

        # define .plugin text strings used for translation
        plugin = _('Alternative Toolbar')
        plugin += "dummy"
        desc = _(
            'Replace the Rhythmbox large toolbar with a Client-Side '
            'Decorated or Compact Toolbar which can be hidden')

        desc += "dummy"
        # stop PyCharm removing the Preference import on optimisation
        pref = Preferences()
        return pref

    def get_toolbar(self, callback):
        """
        a method to return the toolbar itself
        :param callback: function callback - func(AT.ToolbarCallback)
        passed
        :return:
        """

        self.toolbar_type.setup_completed_async(callback)
