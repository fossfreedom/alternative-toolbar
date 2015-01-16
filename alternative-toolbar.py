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

import datetime

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Peas
from gi.repository import PeasGtk
from gi.repository import RB
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import Gio

from alttoolbar_rb3compat import ActionGroup
from alttoolbar_rb3compat import ApplicationShell
import rb


view_menu_ui = """
<ui>
  <menubar name="MenuBar">
    <menu name="ViewMenu" action="View">
      <menuitem name="Show Toolbar" action="ToggleToolbar" />
    </menu>
  </menubar>
</ui>
"""


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
                SHOW_COMPACT='show-compact'
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
        self.settings = self.gs.get_setting(self.gs.Path.PLUGIN)

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
        self.settings.bind(self.gs.PluginKey.START_HIDDEN,
                           start_hidden, 'active', Gio.SettingsBindFlags.DEFAULT)

        show_compact = builder.get_object('show_compact_checkbox')
        self.settings.bind(self.gs.PluginKey.SHOW_COMPACT,
                           show_compact, 'active', Gio.SettingsBindFlags.DEFAULT)

        self.display_type = self.settings[self.gs.PluginKey.DISPLAY_TYPE]
        self.auto_radiobutton = builder.get_object('auto_radiobutton')
        self.headerbar_radiobutton = builder.get_object('headerbar_radiobutton')
        self.toolbar_radiobutton = builder.get_object('toolbar_radiobutton')

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
                self.settings[self.gs.PluginKey.DISPLAY_TYPE] = 0
            elif button == self.headerbar_radiobutton:
                self.settings[self.gs.PluginKey.DISPLAY_TYPE] = 1
            else:
                self.settings[self.gs.PluginKey.DISPLAY_TYPE] = 2


class AltToolbarPlugin(GObject.Object, Peas.Activatable):
    '''
    Main class of the plugin. Manages the activation and deactivation of the
    plugin.
    '''
    __gtype_name = 'AltToolbarPlugin'
    object = GObject.property(type=GObject.Object)

    # signals
    # toolbar-visibility - bool parameter True = visible, False = not visible
    __gsignals__ = {
        'toolbar-visibility': (GObject.SIGNAL_RUN_LAST, None, (bool,))
    }

    # Builder releated utility functions... ####################################

    def load_builder_content(self, builder):
        if ( not hasattr(self, "__builder_obj_names") ):
            self.__builder_obj_names = list()

        for obj in builder.get_objects():
            if ( isinstance(obj, Gtk.Buildable) ):
                name = Gtk.Buildable.get_name(obj).replace(' ', '_')
                self.__dict__[name] = obj
                self.__builder_obj_names.append(name)

    def connect_builder_content(self, builder):
        builder.connect_signals_full(self.connect_builder_content_func, self)

    def connect_builder_content_func(self,
                                     builder,
                                     object,
                                     sig_name,
                                     handler_name,
                                     conn_object,
                                     flags,
                                     target):
        handler = None

        h_name_internal = "_sh_" + handler_name.replace(" ", "_")

        if ( hasattr(target, h_name_internal) ):
            handler = getattr(target, h_name_internal)
        else:
            handler = eval(handler_name)

        object.connect(sig_name, handler)

    def purge_builder_content(self):
        for name in self.__builder_obj_names:
            o = self.__dict__[name]
            if ( isinstance(o, Gtk.Widget) ):
                o.destroy()
            del self.__dict__[name]

        del self.__builder_obj_names


    def __init__(self):
        '''
        Initialises the plugin object.
        '''
        GObject.Object.__init__(self)
        self.gs = GSetting()
        self.settings = self.gs.get_setting(self.gs.Path.PLUGIN)
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
        self.main_window = self.shell.props.window
        # self.main_window.set_border_width(10)

        # Prepare internal variables
        self.song_duration = 0
        self.cover_pixbuf = None
        self.entry = None

        # Prepare Album Art Displaying
        self.album_art_db = GObject.new(RB.ExtDB, name="album-art")

        self.rb_toolbar = self.find(self.shell.props.window,
                                    'main-toolbar', 'by_id')

        builder = Gtk.Builder()
        display_type = self.settings[self.gs.PluginKey.DISPLAY_TYPE]
        start_hidden = self.settings[self.gs.PluginKey.START_HIDDEN]

        default = Gtk.Settings.get_default()

        if display_type == 0:
            if (not default.props.gtk_shell_shows_app_menu) or default.props.gtk_shell_shows_menubar:
                display_type = 2
            else:
                display_type = 1

        print("display type %d" % display_type)

        if display_type == 1:
            ui = rb.find_plugin_file(self, 'ui/altheaderbar.ui')
        else:
            ui = rb.find_plugin_file(self, 'ui/alttoolbar.ui')

        builder.add_from_file(ui)

        self.load_builder_content(builder)
        self.connect_builder_content(builder)

        # Bring Builtin Actions to plugin
        for (a, b) in ((self.play_button, "play"),
                       (self.prev_button, "play-previous"),
                       (self.next_button, "play-next"),
                       (self.repeat_toggle, "play-repeat"),
                       (self.shuffle_toggle, "play-shuffle")):
            a.set_action_name("app." + b)

        self.shell.props.display_page_tree.connect(
            "selected", self.on_page_change
        )

        what, width, height = Gtk.icon_size_lookup(Gtk.IconSize.SMALL_TOOLBAR)

        if display_type == 1:
            self.headerbar = Gtk.HeaderBar.new()
            self.headerbar.set_show_close_button(True)
            self.headerbar.pack_start(self.small_bar)
            self.volume_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
            self.volume_button = Gtk.VolumeButton.new()
            self.volume_button.props.use_symbolic = True
            self.volume_button.set_relief(Gtk.ReliefStyle.NONE)
            self.volume_box.add(self.volume_button)

            self.toolbar_button = Gtk.Button.new_from_icon_name("go-up-symbolic", width)
            self.toolbar_button.set_relief(Gtk.ReliefStyle.NONE)
            self.volume_box.add(self.toolbar_button)

            if (not default.props.gtk_shell_shows_app_menu) or default.props.gtk_shell_shows_menubar:
                # for environments that dont support app-menus
                menu_button = Gtk.MenuButton.new()
                menu_button.set_relief(Gtk.ReliefStyle.NONE)
                image = Gtk.Image.new_from_icon_name("emblem-system-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
                menu_button.add(image)
                menu = self.shell.props.application.get_shared_menu('app-menu')
                menu_button.set_menu_model(menu)
                self.volume_box.add(menu_button)

            self.headerbar.pack_end(self.volume_box)

            # required for Gtk 3.14 to stop RB adding a title to the header bar
            empty = Gtk.DrawingArea.new()
            self.headerbar.set_custom_title(empty)
            self.headerbar.show_all()

            self.main_window.set_titlebar(self.headerbar)  # this is needed for gnome-shell to replace the decoration
            self.rb_toolbar.hide()

        if display_type == 2:
            self.appshell = ApplicationShell(self.shell)
            self.toggle_action_group = ActionGroup(self.shell, 'AltToolbarPluginActions')
            self.toggle_action_group.add_action(func=self.toggle_visibility,
                                                action_name='ToggleToolbar', label=_("Show Toolbar"),
                                                action_state=ActionGroup.TOGGLE,
                                                action_type='app', accel="<Ctrl>t",
                                                tooltip=_("Show or hide the main toolbar"))
            self.appshell.insert_action_group(self.toggle_action_group)
            self.appshell.add_app_menuitems(view_menu_ui, 'AltToolbarPluginActions', 'view')
            action = self.toggle_action_group.get_action('ToggleToolbar')

            self.show_compact_toolbar = self.settings[self.gs.PluginKey.SHOW_COMPACT]

            print("show compact %d" % self.show_compact_toolbar)
            if not start_hidden and self.show_compact_toolbar:
                self.shell.add_widget(self.small_bar,
                                      RB.ShellUILocation.MAIN_TOP, expand=False, fill=False)
                self.small_bar.show_all()
                self.rb_toolbar.hide()
                action.set_active(True)
                print("not hidden but compact")
            elif start_hidden:
                self.rb_toolbar.hide()
                print("hidden")
            else:
                action.set_active(True)
                return

        self.volume_button.bind_property("value", self.shell.props.shell_player, "volume",
                                         Gio.SettingsBindFlags.DEFAULT)
        self.volume_button.props.value = self.shell.props.shell_player.props.volume

        image = self.toolbar_button.get_image()
        if not image:
            image = self.toolbar_button.get_child()

        image.set_pixel_size(width / 2)

        self.sh_tb = self.toolbar_button.connect('clicked', self._sh_on_toolbar_btn_clicked)

        #self.current_page = self.shell.props.display_page_tree.props.model[

        # Connect signal handlers to rhythmbox
        self.shell_player = self.shell.props.shell_player
        self.sh_psc = self.shell_player.connect("playing-song-changed",
                                                self._sh_on_song_change)

        self.sh_op = self.shell_player.connect("elapsed-changed",
                                               self._sh_on_playing)

        self.sh_pc = self.shell_player.connect("playing-changed",
                                               self._sh_on_playing_change)

        self.shell.alternative_toolbar = self

    def _sh_on_toolbar_btn_clicked(self, *args):
        image = self.toolbar_button.get_image()
        if not image:
            image = self.toolbar_button.get_child()

        if image.props.icon_name == 'go-up-symbolic':
            image.props.icon_name = 'go-down-symbolic'
            self.emit('toolbar-visibility', False)

        else:
            image.props.icon_name = 'go-up-symbolic'
            self.emit('toolbar-visibility', True)

        self.on_page_change(self.shell.props.display_page_tree, self.shell.props.selected_page)

    def on_page_change(self, display_page_tree, page):
        toolbar = self.find(page, 'RBSourceToolbar', 'by_name')

        # self.current_page = page
        image = self.toolbar_button.get_image()
        if not image:
            image = self.toolbar_button.get_child()

        if image.props.icon_name == 'go-up-symbolic':
            visible = True
        else:
            visible = False

        if toolbar:
            print("found")
            toolbar.set_visible(visible)
        else:
            print("not found")

    # Couldn't find better way to find widgets than loop through them
    def find(self, node, search_id, search_type):
        print(node.get_name())
        if isinstance(node, Gtk.Buildable):
            if search_type == 'by_id':
                if Gtk.Buildable.get_name(node) == search_id:
                    return node
            elif search_type == 'by_name':
                if node.get_name() == search_id:
                    return node

        if isinstance(node, Gtk.Container):
            for child in node.get_children():
                ret = self.find(child, search_id, search_type)
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
            del self.shell_player

        if self.appshell:
            self.appshell.cleanup()
        self.rb_toolbar.set_visible(True)

        self.purge_builder_content()
        del self.shell
        del self.db

    def toggle_visibility(self, action, param=None, data=None):
        print("toggle_visibility")
        action = self.toggle_action_group.get_action('ToggleToolbar')

        if action.get_active():
            if self.show_compact_toolbar:
                print("show_compact")
                self.shell.add_widget(self.small_bar,
                                      RB.ShellUILocation.MAIN_TOP, expand=False, fill=False)
                self.small_bar.show_all()
            else:
                print("show full")
                self.rb_toolbar.set_visible(True)
        else:
            if self.show_compact_toolbar:
                print("hide compact")
                self.shell.remove_widget(self.small_bar,
                                         RB.ShellUILocation.MAIN_TOP)
            else:
                print("hide full")
                self.rb_toolbar.set_visible(False)

    def display_song(self, entry):
        self.entry = entry

        self.cover_pixbuf = None
        self.album_cover.clear()

        if ( entry is None ):
            self.song_button_label.set_text("")

        else:
            self.song_button_label.set_markup(
                "<b>{title}</b> <small>{album} - {artist}</small>".format(
                    title=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.TITLE)),
                    album=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.ALBUM)),
                    artist=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.ARTIST))))

            key = entry.create_ext_db_key(RB.RhythmDBPropType.ALBUM)
            self.album_art_db.request(key,
                                      self.display_song_album_art_callback,
                                      entry)


    def display_song_album_art_callback(self, key, filename, data, entry):
        if ( ( data is not None ) and ( isinstance(data, GdkPixbuf.Pixbuf) ) ):
            self.cover_pixbuf = data
            scale_cover = self.cover_pixbuf.scale_simple(24, 24,
                                                         GdkPixbuf.InterpType.HYPER)

            self.album_cover.set_from_pixbuf(scale_cover)
        else:
            self.cover_pixbuf = None
            self.album_cover.clear()

        self.album_cover.trigger_tooltip_query()

    # Signal Handlers ##########################################################

    def _sh_on_playing_change(self, player, playing):
        image = self.play_button.get_child()
        if (playing):
            if player.get_active_source().can_pause():
                icon_name = "media-playback-pause-symbolic"
            else:
                icon_name = "media-playback-stop-symbolic"

        else:
            icon_name = "media-playback-start-symbolic"

        image.set_from_icon_name(icon_name, 16)

    def _sh_on_song_change(self, player, entry):
        if ( entry is not None ):
            self.song_duration = entry.get_ulong(RB.RhythmDBPropType.DURATION)
        else:
            self.song_duration = 0
        self.display_song(entry)

    def _sh_on_playing(self, player, second):
        if ( self.song_duration != 0 ):
            self.song_progress.progress = float(second) / self.song_duration

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
                label = "<small>{time}</small>".format(time="%02d:%02d" % (m, s))
                tlabel = "<small>{time}</small>".format(time="%02d:%02d" % (tm, ts))
            else:
                label = "<small>{time}</small>".format(time="%d:%02d:%02d" % (h, m, s))
                tlabel = "<small>{time}</small>".format(time="%d:%02d:%02d" % (th, tm, ts))

            self.current_time_label.set_markup(label)
            self.total_time_label.set_markup(tlabel)

    def _sh_progress_control(self, progress, fraction):
        if ( self.song_duration != 0 ):
            self.shell_player.set_playing_time(self.song_duration * fraction)

    def _sh_bigger_cover(self, cover, x, y, key, tooltip):
        if ( self.cover_pixbuf is not None ):
            tooltip.set_icon(self.cover_pixbuf.scale_simple(300, 300,
                                                            GdkPixbuf.InterpType.HYPER))
            return True
        else:
            return False


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
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.button_pressed = False
        self.button_time = 0
        self.__progress__ = 0

    def do_draw(self, cc):
        alloc = self.get_allocation()
        sc = self.get_style_context()
        fgc = sc.get_background_color(Gtk.StateFlags.SELECTED)  #self.get_state_flags() )
        bgc = sc.get_color(Gtk.StateFlags.NORMAL)  #self.get_state_flags() )

        cc.set_source_rgba(bgc.red, bgc.green, bgc.blue, bgc.alpha)
        cc.rectangle(0, alloc.height / 2, alloc.width, alloc.height / 4)
        cc.fill()

        cc.set_source_rgba(fgc.red, fgc.green, fgc.blue, fgc.alpha)
        cc.rectangle(0, alloc.height / 2, alloc.width * self.progress, alloc.height / 4)
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

