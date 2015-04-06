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

from datetime import datetime, date

from gi.repository import Gtk

from gi.repository import GObject
from gi.repository import RB
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import Gio
from gi.repository import Gdk

from alttoolbar_rb3compat import gtk_version

from alttoolbar_controller import AltGenericController
from alttoolbar_controller import AltMusicLibraryController
from alttoolbar_controller import AltSoundCloudController
from alttoolbar_controller import AltCoverArtBrowserController
from alttoolbar_widget import SmallProgressBar
from alttoolbar_widget import SmallScale
import rb


class AltToolbarBase(GObject.Object):
    '''
    base for all toolbar types - never instantiated by itself
    '''

    def __init__(self):
        '''
        Initialises the object.
        '''
        super(AltToolbarBase, self).__init__()

        self.source_toolbar_visible = True

    def initialise(self, plugin):
        '''
          one off initialisation call

          :param plugin is the plugin reference
        '''

        self.plugin = plugin
        self.shell = plugin.shell

        self.find = plugin.find

        action = self.plugin.toggle_action_group.get_action('ToggleSourceMediaToolbar')
        action.set_active(self.source_toolbar_visible)

    def post_initialise(self):
        '''
          one off post initialisation call
        '''
        pass

    def set_visible(self, visible):
        '''
           change the visibility of the toolbar
           :param bool
        '''
        pass

    def show_cover(self, visible):
        '''
           change the visibility of the toolbar coverart
           :param bool
        '''
        pass

    def display_song(self, visible):
        '''
           change the visibility of the song label on the toolbar
           :param bool
        '''
        pass

    def play_control_change(self, player, playing):
        '''
           control the display of various play-controls
           :param player is the shell-player
           :param playing bool as to whether a track is being played
        '''
        pass

    def purge_builder_content(self):
        '''
           one off cleanup routine called when the plugin in deactivated
        '''
        pass

    def show_slider(self, visible):
        '''
           show or hide the slider (progress bar)
           :param visible is a bool
        '''
        pass

    def reset_toolbar(self, page):
        '''
           whenever a source changes this resets the toolbar to reflect the changed source
           :param RBDisplayPage
        '''
        if not page:
            return

        toolbar = self.find(page, 'RBSourceToolbar', 'by_name')

        if toolbar:
            print("found")
            toolbar.set_visible(not self.source_toolbar_visible)
        else:
            print("not found")

        self.plugin.emit('toolbar-visibility', not self.source_toolbar_visible)

    def toggle_source_toolbar(self):
        '''
           called to toggle the source toolbar
        '''
        self.source_toolbar_visible = not self.source_toolbar_visible
        self.plugin.on_page_change(self.shell.props.display_page_tree, self.shell.props.selected_page)


class AltToolbarStandard(AltToolbarBase):
    '''
    standard RB toolbar
    '''
    __gtype_name = 'AltToolbarStandard'

    def __init__(self):
        '''
        Initialises the object.
        '''
        super(AltToolbarStandard, self).__init__()

    def post_initialise(self):
        self.volume_button = self.find(self.plugin.rb_toolbar, 'GtkVolumeButton', 'by_id')
        self.volume_button.set_visible(self.plugin.volume_control)

        action = self.plugin.toggle_action_group.get_action('ToggleToolbar')
        action.set_active(not self.plugin.start_hidden)

        self.set_visible(not self.plugin.start_hidden)

    def set_visible(self, visible):
        self.plugin.rb_toolbar.set_visible(visible)


class AltToolbarShared(AltToolbarBase):
    '''
    shared components for the compact and headerbar toolbar types
    '''

    def __init__(self):
        '''
        Initialises the object.
        '''
        super(AltToolbarShared, self).__init__()

        # Prepare Album Art Displaying
        self.album_art_db = GObject.new(RB.ExtDB, name="album-art")

        what, width, height = Gtk.icon_size_lookup(Gtk.IconSize.SMALL_TOOLBAR)
        self.icon_width = width
        self.cover_pixbuf = None

    def initialise(self, plugin):
        super(AltToolbarShared, self).initialise(plugin)

        ui = rb.find_plugin_file(plugin, 'ui/alttoolbar.ui')

        builder = Gtk.Builder()
        builder.add_from_file(ui)

        self.load_builder_content(builder)
        self.connect_builder_content(builder)

    def post_initialise(self):
        self.volume_button.bind_property("value", self.shell.props.shell_player, "volume",
                                         Gio.SettingsBindFlags.DEFAULT)
        self.volume_button.props.value = self.shell.props.shell_player.props.volume
        self.volume_button.set_visible(self.plugin.volume_control)
        self.volume_button.set_relief(Gtk.ReliefStyle.NORMAL)

        if self.plugin.inline_label:
            self.song_box.remove(self.song_button_label)

        if self.plugin.compact_progressbar:
            self.song_progress = SmallProgressBar()
        else:
            self.song_progress = SmallScale()

        self.song_progress.connect('control', self._sh_progress_control)
        self.song_progress.show_all()
        self.song_progress_box.pack_start(self.song_progress, False, True, 1)


        # Bring Builtin Actions to plugin
        for (a, b) in ((self.play_button, "play"),
                       (self.prev_button, "play-previous"),
                       (self.next_button, "play-next"),
                       (self.repeat_toggle, "play-repeat"),
                       (self.shuffle_toggle, "play-shuffle")):
            a.set_action_name("app." + b)
            if b == "play-repeat" or b == "play-shuffle":
                # for some distros you need to set the target_value
                # for others this would actually disable the action
                # so work around this by testing if the action is disabled
                # then reset the action
                a.set_action_target_value(GLib.Variant("b", True))
                print(a.get_sensitive())
                if not a.get_sensitive():
                    a.set_detailed_action_name("app." + b)

    def show_cover_tooltip(self, tooltip):
        if ( self.cover_pixbuf is not None ):
            print("cover_pixbuf")
            tooltip.set_icon(self.cover_pixbuf.scale_simple(300, 300,
                                                            GdkPixbuf.InterpType.HYPER))
            return True
        else:
            return False

    def show_slider(self, visibility):
        self.song_box.set_visible(visibility)

    def display_song(self, entry):
        self.entry = entry

        self.cover_pixbuf = None
        self.album_cover.clear()

        if self.plugin.inline_label:
            ret = self._inline_progress_label(entry)
        else:
            ret = self._combined_progress_label(entry)

        if ret:
            key = entry.create_ext_db_key(RB.RhythmDBPropType.ALBUM)
            self.album_art_db.request(key,
                                      self.display_song_album_art_callback,
                                      entry)

    def _inline_progress_label(self, entry):

        if ( entry is None ):
            # self.song_button_label.set_text("")
            self.inline_box.set_visible(False)
            return False

        self.inline_box.set_visible(True)

        stream_title = self.shell.props.db.entry_request_extra_metadata(entry, RB.RHYTHMDB_PROP_STREAM_SONG_TITLE)
        stream_artist = self.shell.props.db.entry_request_extra_metadata(entry, RB.RHYTHMDB_PROP_STREAM_SONG_ARTIST)

        if stream_title:
            if stream_artist:
                artist_markup = "<small>{artist}</small>".format(
                    artist=GLib.markup_escape_text(stream_artist))
            else:
                artist_markup = ""

            title_markup = "<small><b>{title}</b></small>".format(
                title=GLib.markup_escape_text(stream_title))

            self.song_title.set_markup(title_markup)
            self.song_artist.set_markup(artist_markup)

            return True

        album = entry.get_string(RB.RhythmDBPropType.ALBUM)
        if not album or album == "":
            self.song_title.set_markup("<small><b>{title}</b></small>".format(
                title=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.TITLE))))
            self.song_artist.set_label("")
            return True

        if self.plugin.playing_label:
            year = entry.get_ulong(RB.RhythmDBPropType.DATE)
            if year == 0:
                year = date.today().year
            else:
                year = datetime.fromordinal(year).year

            self.song_title.set_markup(
                "<small>{album}</small>".format(
                    album=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.ALBUM))))
            self.song_artist.set_markup(
                "<small>{genre} - {year}</small>".format(
                    genre=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.GENRE)),
                    year=GLib.markup_escape_text(str(year))))
        else:
            self.song_title.set_markup(
                "<small><b>{title}</b></small>".format(
                    title=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.TITLE))))

            self.song_artist.set_markup(
                "<small>{artist}</small>".format(
                    artist=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.ARTIST))))

        return True


    def _combined_progress_label(self, entry):
        '''
           utility function to calculate the label to be used when a progress bar has the label above it
           :param RBEntry
        '''

        if ( entry is None ):
            self.song_button_label.set_text("")
            return False

        stream_title = self.shell.props.db.entry_request_extra_metadata(entry, RB.RHYTHMDB_PROP_STREAM_SONG_TITLE)
        stream_artist = self.shell.props.db.entry_request_extra_metadata(entry, RB.RHYTHMDB_PROP_STREAM_SONG_ARTIST)

        if stream_title:
            if stream_artist:
                markup = "<small><b>{title}</b> {artist}</small>".format(
                    title=GLib.markup_escape_text(stream_title),
                    artist=GLib.markup_escape_text(stream_artist))
            else:
                markup = "<small><b>{title}</b></small>".format(
                    title=GLib.markup_escape_text(stream_title))
            self.song_button_label.set_markup(markup)
            return True

        album = entry.get_string(RB.RhythmDBPropType.ALBUM)
        if not album or album == "":
            self.song_button_label.set_markup("<small><b>{title}</b></small>".format(
                title=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.TITLE))))
            return True

        if self.plugin.playing_label:
            year = entry.get_ulong(RB.RhythmDBPropType.DATE)
            if year == 0:
                year = date.today().year
            else:
                year = datetime.fromordinal(year).year

            self.song_button_label.set_markup(
                "<small>{album} - {genre} - {year}</small>".format(
                    album=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.ALBUM)),
                    genre=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.GENRE)),
                    year=GLib.markup_escape_text(str(year))))
        else:
            self.song_button_label.set_markup(
                "<small><b>{title}</b> {album} - {artist}</small>".format(
                    title=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.TITLE)),
                    album=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.ALBUM)),
                    artist=GLib.markup_escape_text(entry.get_string(RB.RhythmDBPropType.ARTIST))))

        return True

    def display_song_album_art_callback(self, *args):  # key, filename, data, entry):
        '''
          RBExtDB signal callback to display the album-art
        '''
        # rhythmbox 3.2 breaks the API - need to find the parameter with the pixbuf
        data = None
        for data in args:
            if isinstance(data, GdkPixbuf.Pixbuf):
                break

        if ( ( data is not None ) and ( isinstance(data, GdkPixbuf.Pixbuf) ) ):
            self.cover_pixbuf = data
            scale_cover = self.cover_pixbuf.scale_simple(34, 34,
                                                         GdkPixbuf.InterpType.HYPER)

            self.album_cover.set_from_pixbuf(scale_cover)
        else:
            self.cover_pixbuf = None
            self.album_cover.clear()

        self.album_cover.trigger_tooltip_query()


    def show_cover(self, visibility):
        self.album_cover.set_visible(self.plugin.show_album_art)

    def show_small_bar(self):
        self.small_bar.show_all()
        self.inline_box.set_visible(False)


    def play_control_change(self, player, playing):
        image = self.play_button.get_child()
        if (playing):
            if player.get_active_source().can_pause():
                icon_name = "media-playback-pause-symbolic"
            else:
                icon_name = "media-playback-stop-symbolic"

        else:
            icon_name = "media-playback-start-symbolic"

        image.set_from_icon_name(icon_name, image.props.icon_size)

    # Builder related utility functions... ####################################

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

    # Signal Handlers ##########################################################

    def _sh_progress_control(self, progress, fraction):
        #if not hasattr(self, 'song_duration'):
        #    return

        if ( self.plugin.song_duration != 0 ):
            self.shell.props.shell_player.set_playing_time(self.plugin.song_duration * fraction)

    def _sh_bigger_cover(self, cover, x, y, key, tooltip):
        return self.show_cover_tooltip(tooltip)


class AltToolbarCompact(AltToolbarShared):
    '''
    compact RB toolbar
    '''
    __gtype_name = 'AltToolbarCompact'

    def __init__(self):
        '''
        Initialises the object.
        '''
        super(AltToolbarCompact, self).__init__()

    def initialise(self, plugin):
        super(AltToolbarCompact, self).initialise(plugin)

        self._setup_compactbar()

    def _setup_compactbar(self):

        # self.window_control_item.add(self._window_controls())

        action = self.plugin.toggle_action_group.get_action('ToggleToolbar')

        self.small_bar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)

        if not self.plugin.start_hidden:
            self.shell.add_widget(self.small_bar,
                                  RB.ShellUILocation.MAIN_TOP, expand=False, fill=False)
            self.show_small_bar()
            action.set_active(True)
            print("not hidden but compact")
        else:
            action.set_active(False)

        self.plugin.rb_toolbar.hide()

    def set_visible(self, visible):
        if visible:
            print("show_compact")
            self.shell.add_widget(self.small_bar,
                                  RB.ShellUILocation.MAIN_TOP, expand=False, fill=False)
            self.show_small_bar()
            self.volume_button.set_visible(self.plugin.volume_control)
        else:
            print("hide compact")
            self.shell.remove_widget(self.small_bar,
                                     RB.ShellUILocation.MAIN_TOP)


class AltToolbarHeaderBar(AltToolbarShared):
    '''
    headerbar RB toolbar
    '''
    __gtype_name = 'AltToolbarHeaderBar'

    def __init__(self):
        '''
        Initialises the object.
        '''
        super(AltToolbarHeaderBar, self).__init__()

        self.sources = {}
        self._controllers = {}
        self.searchbar = None

        self.source_toolbar_visible = False  # override - for headerbars source toolbar is not visible


    def initialise(self, plugin):
        super(AltToolbarHeaderBar, self).initialise(plugin)

        self.main_window = self.shell.props.window

        self._controllers['generic'] = AltGenericController(self)
        # every potential source should have its own controller to manage the headerbar controls
        # where a controller is not specified then a generic controller is used
        # i.e. use add_controller method to add a controller
        self.add_controller(AltMusicLibraryController(self))
        self.add_controller(AltSoundCloudController(self))
        self.add_controller(AltCoverArtBrowserController(self))

        self._setup_playbar()
        self._setup_headerbar()
        
        # hook the key-press for the application window
        self.shell.props.window.connect("key-press-event", self._on_key_press)

        # finally - complete the headerbar setup after the database has fully loaded because
        # rhythmbox has everything initiated at this point.

        self.shell.props.db.connect('load-complete', self._load_complete)
        
    def _on_key_press(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname == 'Escape' and self.current_search_button:
            self.current_search_button.set_active(False)
        if event.state and Gdk.ModifierType.CONTROL_MASK:
            if keyname == 'f' and self.current_search_button:
                self.current_search_button.set_active(True)
        

    def _load_complete(self, *args):
        self._set_toolbar_controller()

    def _setup_playbar(self):
        '''
          setup the play controls at the bottom part of the application
        '''

        box = self.find(self.shell.props.window,
                        'GtkBox', 'by_name')
        frame_box = Gtk.Box()
        frame_box.set_orientation(Gtk.Orientation.VERTICAL)
        self.small_frame = Gtk.Frame()
        self.small_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        frame_box.pack_start(self.small_frame, False, True, 0)
        frame_box.pack_start(self.small_bar, False, True, 1)
        box.pack_start(frame_box, False, True, 0)
        box.reorder_child(frame_box, 3)

        frame_box.show_all()
        self.show_small_bar()

        # hide status bar
        action = self.plugin.appshell.lookup_action('', 'statusbar-visible', 'win')
        action.set_active(True)

    def search_button_toggled(self, search_button):
        print("search_button_toggled")
        print(search_button.get_active())
        self.searchbar.set_search_mode(search_button.get_active())

    def library_radiobutton_toggled(self, toggle_button):
        print("library_radiobutton_toggled")
        if not hasattr(self, 'library_song_radiobutton'):
            return  # kludge = fix this later

        val, button = self.is_browser_view(self.shell.props.selected_page)
        if not val:
            return

        val = True
        if self.library_song_radiobutton.get_active():
            val = False

        self.shell.props.selected_page.props.show_browser = val

    def has_button_with_label(self, source, label):
        '''
           returns bool, button where the button has a given label
        '''
        if not source:
            return False, None

        toolbar = self.find(source, 'RBSourceToolbar', 'by_name')
        if not toolbar:
            return False, None

        ret = self.find(toolbar, 'GtkToggleButton', 'by_name', label)

        if ret:
            return True, ret

        ret = self.find(toolbar, 'GtkButton', 'by_name', label)

        if ret:
            return True, ret

        ret = self.find(toolbar, 'GtkMenuButton', 'by_name', label)

        if ret:
            return True, ret

        return False, None

    def is_browser_view(self, source):
        '''
           returns bool, browser-button where this is a browser-view
           i.e. assume if there is a browser button this makes it a browser-view
        '''

        return self.has_button_with_label(source, _("Browse"))

    def _setup_headerbar(self):
        default = Gtk.Settings.get_default()
        self.headerbar = Gtk.HeaderBar.new()
        self.headerbar.set_show_close_button(True)

        self.main_window.set_titlebar(self.headerbar)  # this is needed for gnome-shell to replace the decoration
        self.plugin.rb_toolbar.hide()

        self.headerbar.set_custom_title(self.library_box)

        self._end_box_controls = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)  # right side box
        self.end_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)  # any source defined controls
        self._end_box_controls.add(self.end_box)

        if (not default.props.gtk_shell_shows_app_menu) or default.props.gtk_shell_shows_menubar:

            # for environments that dont support app-menus
            menu_button = Gtk.MenuButton.new()
            menu_button.set_relief(Gtk.ReliefStyle.NONE)
            if gtk_version() >= 3.14:
                symbol = "open-menu-symbolic"
            else:
                symbol = "emblem-system-symbolic"

            image = Gtk.Image.new_from_icon_name(symbol, Gtk.IconSize.SMALL_TOOLBAR)
            menu_button.add(image)
            menu = self.shell.props.application.get_shared_menu('app-menu')
            menu_button.set_menu_model(menu)
            self._end_box_controls.add(menu_button)

        self.headerbar.pack_end(self._end_box_controls)
        self.headerbar.show_all()

        action = self.plugin.toggle_action_group.get_action('ToggleToolbar')
        if not self.plugin.start_hidden:
            action.set_active(True)
            print("not hidden")
        else:
            action.set_active(False)
            self.set_visible(False)

    def reset_toolbar(self, page):
        print(page)
        super(AltToolbarHeaderBar, self).reset_toolbar(page)

        self.library_radiobutton_toggled(None)

        self._set_toolbar_controller()

    def _set_toolbar_controller(self):
        if 'generic' not in self._controllers:
            return

        current_controller = None

        if not self.shell.props.selected_page in self.sources:
            # loop through controllers to find one that is most applicable

            found = False
            for controller_type in self._controllers:
                print(controller_type)
                if self._controllers[controller_type].valid_source(self.shell.props.selected_page):
                    self.sources[self.shell.props.selected_page] = self._controllers[controller_type]
                    found = True
                    break

            if not found:
                self.sources[self.shell.props.selected_page] = self._controllers['generic']

        current_controller = self.sources[self.shell.props.selected_page]
        current_controller.update_controls(self.shell.props.selected_page)

    def set_visible(self, visible):
        self.small_bar.set_visible(visible)

    def add_controller(self, controller):
        if not controller in self._controllers:
            self._controllers[controller] = controller
