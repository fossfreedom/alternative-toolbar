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

import math

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Peas
from gi.repository import PeasGtk
from gi.repository import RB
from gi.repository import Gdk
from gi.repository import Gio

from alttoolbar_rb3compat import ActionGroup
from alttoolbar_rb3compat import ApplicationShell
from alttoolbar_type import AltToolbarStandard
from alttoolbar_type import AltToolbarCompact
from alttoolbar_type import AltToolbarHeaderBar
import rb


view_menu_ui = """
<ui>
  <menubar name="MenuBar">
    <menu name="ViewMenu" action="View">
        <menuitem name="Show Toolbar" action="ToggleToolbar" />
        <menuitem name="Show Source and Media Toolbar" action="ToggleSourceMediaToolbar" />
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
                INLINE_LABEL='inline-label'
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

        inline_label = builder.get_object('inline_label_checkbutton')
        self.plugin_settings.bind(self.gs.PluginKey.INLINE_LABEL,
                                  inline_label, 'active', Gio.SettingsBindFlags.DEFAULT)

        volume_control = builder.get_object('volume_control_checkbox')
        self.plugin_settings.bind(self.gs.PluginKey.VOLUME_CONTROL,
                                  volume_control, 'active', Gio.SettingsBindFlags.DEFAULT)

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


class AltToolbarPlugin(GObject.Object, Peas.Activatable):
    '''
    Main class of the plugin. Manages the activation and deactivation of the
    plugin.
    '''
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
        '''
        Initialises the plugin object.
        '''
        GObject.Object.__init__(self)
        self.appshell = None
        self.sh_psc = self.sh_op = self.sh_pc = None

    def do_activate(self):
        '''
        Called by Rhythmbox when the plugin is activated. It creates the
        plugin's source and connects signals to manage the plugin's
        preferences.
        '''

        self.shell = self.object
        self.db = self.shell.props.db

        # Prepare internal variables
        self.song_duration = 0
        self.entry = None

        self.rb_toolbar = AltToolbarPlugin.find(self.shell.props.window,
                                                'main-toolbar', 'by_id')

        displaypagetree = AltToolbarPlugin.find(self.shell.props.window,
                                                'RBDisplayPageTree', 'by_name')
        self.sourcemedia_toolbar = AltToolbarPlugin.find(displaypagetree,
                                                         'GtkToolbar', 'by_name')
        self.sourcemedia_toolbar.set_visible(False)

        self.gs = GSetting()
        self.plugin_settings = self.gs.get_setting(self.gs.Path.PLUGIN)

        # get values from gsettings
        display_type = self.plugin_settings[self.gs.PluginKey.DISPLAY_TYPE]
        self.volume_control = self.plugin_settings[self.gs.PluginKey.VOLUME_CONTROL]
        self.show_compact_toolbar = self.plugin_settings[self.gs.PluginKey.SHOW_COMPACT]
        self.start_hidden = self.plugin_settings[self.gs.PluginKey.START_HIDDEN]
        self.inline_label = self.plugin_settings[self.gs.PluginKey.INLINE_LABEL]

        default = Gtk.Settings.get_default()

        if display_type == 0:
            if (not default.props.gtk_shell_shows_app_menu) or default.props.gtk_shell_shows_menubar:
                display_type = 2
            else:
                display_type = 1

        print("display type %d" % display_type)

        self.appshell = ApplicationShell(self.shell)
        self._add_menu_options()

        self.toolbar_type = None
        if display_type == 1:
            self.toolbar_type = AltToolbarHeaderBar()
            # every potential source should have its own controller to manage the headerbar controls
            # where a controller is not specified then a generic controller is used
            # i.e. use add_controller method to add a controller

        elif self.show_compact_toolbar:
            self.toolbar_type = AltToolbarCompact()
        else:
            self.toolbar_type = AltToolbarStandard()

        self.toolbar_type.initialise(self)
        self.toolbar_type.post_initialise()

        self.shell_player = self.shell.props.shell_player

        self._connect_signals()
        self._connect_properties()

        # allow other plugins access to this toolbar
        self.shell.alternative_toolbar = self


    def _add_menu_options(self):
        self.seek_action_group = ActionGroup(self.shell, 'AltToolbarPluginSeekActions')
        self.seek_action_group.add_action(func=self.on_skip_backward,
                                          action_name='SeekBackward', label=_("Seek Backward"),
                                          action_type='app', accel="<Alt>Left",
                                          tooltip=_("Seek backward, in current track, by 5 seconds."))
        self.seek_action_group.add_action(func=self.on_skip_forward,
                                          action_name='SeekForward', label=_("Seek Forward"),
                                          action_type='app', accel="<Alt>Right",
                                          tooltip=_("Seek forward, in current track, by 10 seconds."))

        self.appshell.insert_action_group(self.seek_action_group)
        self.appshell.add_app_menuitems(view_seek_menu_ui, 'AltToolbarPluginSeekActions', 'view')

        self.toggle_action_group = ActionGroup(self.shell, 'AltToolbarPluginActions')
        self.toggle_action_group.add_action(func=self.toggle_visibility,
                                            action_name='ToggleToolbar', label=_("Show Play-Controls Toolbar"),
                                            action_state=ActionGroup.TOGGLE,
                                            action_type='app',
                                            tooltip=_("Show or hide the main toolbar"))
        self.toggle_action_group.add_action(func=self.toggle_sourcemedia_visibility,
                                            action_name='ToggleSourceMediaToolbar',
                                            label=_("Show Source and Media Toolbars"),
                                            action_state=ActionGroup.TOGGLE,
                                            action_type='app', accel="<Ctrl>t",
                                            tooltip=_("Show or hide the source and media toolbars"))

        self.appshell.insert_action_group(self.toggle_action_group)
        self.appshell.add_app_menuitems(view_menu_ui, 'AltToolbarPluginActions', 'view')


    def _connect_properties(self):
        self.plugin_settings.bind(self.gs.PluginKey.PLAYING_LABEL, self, 'playing_label',
                                  Gio.SettingsBindFlags.GET)

    def _connect_signals(self):
        self.sh_display_page_tree = self.shell.props.display_page_tree.connect(
            "selected", self.on_page_change
        )

        self.sh_psc = self.shell_player.connect("playing-song-changed",
                                                self._sh_on_song_change)

        self.sh_op = self.shell_player.connect("elapsed-changed",
                                               self._sh_on_playing)

        self.sh_pc = self.shell_player.connect("playing-changed",
                                               self._sh_on_playing_change)

        self.sh_pspc = self.shell_player.connect("playing-song-property-changed",
                                                 self._sh_on_song_property_changed)

        self.rb_settings = Gio.Settings.new('org.gnome.rhythmbox')
        # tried to connect directly to changed signal but never seems to be fired
        # so have to use bind and notify method to detect key changes
        # self.rb_settings.bind('display-page-tree-visible', self, 'display_page_tree_visible',
        #             Gio.SettingsBindFlags.GET)
        #self.sh_display_page = self.connect('notify::display-page-tree-visible', self.display_page_tree_visible_settings_changed)

        self.rb_settings.bind('show-album-art', self, 'show_album_art',
                              Gio.SettingsBindFlags.GET)
        self.connect('notify::show-album-art', self.show_album_art_settings_changed)
        self.show_album_art_settings_changed(None)

        self.rb_settings.bind('show-song-position-slider', self, 'show_song_position_slider',
                              Gio.SettingsBindFlags.GET)
        self.connect('notify::show-song-position-slider', self.show_song_position_slider_settings_changed)
        self.show_song_position_slider_settings_changed(None)

        #self.display_page_tree_visible_settings_changed(None)

    def _sh_on_song_property_changed(self, sp, uri, property, old, new):
        if sp.get_playing() and property in ('artist',
                                             'album',
                                             'title',
                                             RB.RHYTHMDB_PROP_STREAM_SONG_ARTIST,
                                             RB.RHYTHMDB_PROP_STREAM_SONG_ALBUM,
                                             RB.RHYTHMDB_PROP_STREAM_SONG_TITLE):
            entry = sp.get_playing_entry()
            self.display_song(entry)

    def _sh_on_playing_change(self, player, playing):
        self.toolbar_type.play_control_change(player, playing)

    def _sh_on_song_change(self, player, entry):
        if ( entry is not None ):
            self.song_duration = entry.get_ulong(RB.RhythmDBPropType.DURATION)
        else:
            self.song_duration = 0

        self.toolbar_type.display_song(entry)

    def _sh_on_playing(self, player, second):
        if not hasattr(self.toolbar_type, 'song_progress'):
            return

        if ( self.song_duration != 0 ):
            self.toolbar_type.song_progress.progress = float(second) / self.song_duration

            try:
                valid, time = player.get_playing_time()
                if not valid or time == 0:
                    return
            except:
                return

            m, s = divmod(time, 60)
            h, m = divmod(m, 60)

            tm, ts = divmod(self.song_duration, 60)
            th, tm = divmod(tm, 60)

            if th == 0:
                label = "<small>{time} / {ttime}</small>".format(time="%02d:%02d" % (m, s),
                                                                 ttime="%02d:%02d" % (tm, ts))
                # tlabel = "<small>{time}</small>".format(time="%02d:%02d" % (tm, ts))
            else:
                label = "<small>{time}</small>".format(time="%d:%02d:%02d" % (h, m, s))
                tlabel = "<small>{time} / {ttime}</small>".format(time="%d:%02d:%02d" % (h, m, s),
                                                                  ttime="%d:%02d:%02d" % (th, tm, ts))

            # self.toolbar_type.current_time_label.set_markup(label)
            self.toolbar_type.total_time_label.set_markup(label)

    def on_skip_backward(self, *args):
        sp = self.object.props.shell_player
        if ( sp.get_playing()[1] ):
            seek_time = sp.get_playing_time()[1] - seek_backward_time
            print(seek_time)
            if ( seek_time < 0 ): seek_time = 0

            print(seek_time)
            sp.set_playing_time(seek_time)

    def on_skip_forward(self, *args):
        sp = self.object.props.shell_player
        if ( sp.get_playing()[1] ):
            seek_time = sp.get_playing_time()[1] + seek_forward_time
            song_duration = sp.get_playing_song_duration()
            if ( song_duration > 0 ):  # sanity check
                if ( seek_time > song_duration ): seek_time = song_duration

                sp.set_playing_time(seek_time)

    def show_song_position_slider_settings_changed(self, *args):
        self.toolbar_type.show_slider(self.show_song_position_slider)

    # def display_page_tree_visible_settings_changed(self, *args):
    #    self.toolbar_type.toggle_sidepane(self.display_page_tree_visible)

    def show_album_art_settings_changed(self, *args):
        self.toolbar_type.show_cover(self.show_album_art)

    def on_page_change(self, display_page_tree, page):
        print("page changed")
        self.toolbar_type.reset_toolbar(page)

    @staticmethod
    def find(node, search_id, search_type, button_label=None):
        # Couldn't find better way to find widgets than loop through them
        print("by_name %s by_id %s" % (node.get_name(), Gtk.Buildable.get_name(node)))

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
                    if button_label == None or ('Button' in node.get_name() and extract_label(node) == button_label):
                        return node
            elif search_type == 'by_name':
                if node.get_name() == search_id:
                    if button_label == None or ('Button' in node.get_name() and extract_label(node) == button_label):
                        return node

        if isinstance(node, Gtk.Container):
            for child in node.get_children():
                ret = AltToolbarPlugin.find(child, search_id, search_type, button_label)
                if ret:
                    return ret

        return None

    def do_deactivate(self):
        '''
        Called by Rhythmbox when the plugin is deactivated. It makes sure to
        free all the resources used by the plugin.
        '''
        if self.sh_op:
            self.shell_player.disconnect(self.sh_op)
            self.shell_player.disconnect(self.sh_psc)
            self.shell_player.disconnect(self.sh_pc)
            self.shell_player.disconnect(self.sh_pspc)
            #self.disconnect(self.sh_display_page)
            self.shell.props.display_page_tree.disconnect(self.sh_display_page_tree)
            del self.shell_player

        if self.appshell:
            self.appshell.cleanup()

        self.rb_toolbar.set_visible(True)
        self.sourcemedia_toolbar.set_visible(True)

        self.toolbar_type.purge_builder_content()

        del self.shell
        del self.db

    def toggle_visibility(self, action, param=None, data=None):
        print("toggle_visibility")
        action = self.toggle_action_group.get_action('ToggleToolbar')

        self.toolbar_type.set_visible(action.get_active())

    def toggle_sourcemedia_visibility(self, action, param=None, data=None):
        print("toggle_sourcemedia_visibility")
        action = self.toggle_action_group.get_action('ToggleSourceMediaToolbar')

        self.sourcemedia_toolbar.set_visible(action.get_active())
        self.toolbar_type.toggle_source_toolbar()


# ###############################################################################
# Custom Widgets ###############################################################

class SmallProgressBar(Gtk.DrawingArea):
    __gsignals__ = {
        "control": (GObject.SIGNAL_RUN_LAST, None, (float,))
    }

    @GObject.Property
    def progress(self):
        return self.__progress__

    @progress.setter
    def progress(self, value):
        self.__progress__ = value
        self.queue_draw()

    def __init__(self):
        super(SmallProgressBar, self).__init__()
        print("############")
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.button_pressed = False
        self.button_time = 0
        self.__progress__ = 0

    def do_draw(self, cc):
        alloc = self.get_allocation()
        sc = self.get_style_context()
        fgc = sc.get_background_color(Gtk.StateFlags.SELECTED)  # self.get_state_flags() )
        bgc = sc.get_color(Gtk.StateFlags.NORMAL)  # self.get_state_flags() )

        cc.set_source_rgba(bgc.red, bgc.green, bgc.blue, bgc.alpha)

        print(alloc.height)
        offset = int(alloc.height / 2)
        print(offset)
        cc.rectangle(0, offset, alloc.width, 2)
        cc.fill()

        cc.set_source_rgba(fgc.red, fgc.green, fgc.blue, fgc.alpha)
        cc.rectangle(0, offset, alloc.width * self.progress, 2)
        cc.fill()

        if self.progress != 0:
            cc.set_line_width(1)
            cc.set_source_rgba(bgc.red, bgc.green, bgc.blue, bgc.alpha)

            cc.translate((alloc.width * self.progress), offset + 1)
            print(self.progress)
            cc.arc(0, 0, 4, 0, 2 * math.pi)
            cc.stroke_preserve()

            cc.fill()

    def do_motion_notify_event(self, event):
        if ( self.button_pressed ):
            self.control_by_event(event)
            return True
        else:
            return False

    def do_button_press_event(self, event):
        self.button_pressed = True
        self.control_by_event(event)
        return True

    def do_button_release_event(self, event):
        self.button_pressed = False
        self.control_by_event(event)
        return True

    def control_by_event(self, event):
        allocw = self.get_allocated_width()
        fraction = event.x / allocw
        if ( self.button_time + 100 < event.time ):
            self.button_time = event.time
            self.emit("control", fraction)

