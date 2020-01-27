# This is a part of the external Repeat One Song plugin for Rhythmbox
#
# Author: Eduardo Mucelli Rezende Oliveira
# E-mail: edumucelli@gmail.com or eduardom@dcc.ufmg.br
# Version: 0.4 (Unstable) for Rhythmbox 3.0.1 or later
#
# reworked for alternative-toolbar
# Author: David Mohammed 2015-2020 <fossfreedom@ubuntu.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from alttoolbar_preferences import CoverLocale
from alttoolbar_preferences import GSetting
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import Gtk


class Repeat(GObject.Object):
    """
    Object handling song repeating, with an additional feature of
    repeating one song, one song only.
    """

    SONG_CHANGED_MANUAL = 0
    SONG_CHANGED_EOS = 1

    def __init__(self, shell, toggle_button):
        """
        :param shell: the plugin object
        :param toggle_button: button that controls the repeat functions
        """
        GObject.Object.__init__(self)

        # use this to start the repeat-one-song capability (if True)
        self.repeat_song = False
        self.toggle_button = toggle_button
        self.song_changed = self.SONG_CHANGED_MANUAL

        player = shell.props.shell_player
        # EOS signal means that the song changed because the song is over.
        # ie. the user did not manually change the song.
        # https://developer.gnome.org/rhythmbox/unstable/RBPlayer.html#RBPlayer-eos
        player.props.player.connect('eos', self.on_gst_player_eos)
        player.connect('playing-song-changed', self.on_song_change)
        # This hack is no longer needed when the above signal handlers
        # work. For more details, refer to the comments above the
        # definition of method on_elapsed_change.
        # player.connect('elapsed-changed', self.on_elapsed_change)

        try:
            popover = Gtk.Popover.new(toggle_button)
        except AttributeError:
            # use our custom Popover equivalent for Gtk+3.10 folks
            popover = CustomPopover(toggle_button)
        else:
            popover.set_modal(False)
        finally:
            repeat = RepeatPopContainer(popover, toggle_button)
            popover.add(repeat)

        toggle_button.connect('toggled', self._on_toggle, popover, repeat)
        repeat.connect('repeat-type-changed', self._on_repeat_type_changed)

        self._on_repeat_type_changed(repeat, repeat.get_repeat_type())

    def _on_toggle(self, toggle, popover, repeat):
        if toggle.get_active():
            popover.show_all()
            self.repeat_song = \
                repeat.get_repeat_type() == RepeatPopContainer.ONE_SONG
        else:
            popover.hide()
            self.repeat_song = False

        self._set_toggle_tooltip(repeat)

        print("on toggle", self.repeat_song)

    def _set_toggle_tooltip(self, repeat):
        # locale stuff
        cl = CoverLocale()
        cl.switch_locale(cl.Locale.LOCALE_DOMAIN)
        if self.toggle_button.get_has_tooltip():
            if repeat.get_repeat_type() == RepeatPopContainer.ALL_SONGS:
                message = _("Repeat all tracks")
            else:
                message = _("Repeat the current track")
            self.toggle_button.set_tooltip_text(message)
        cl = CoverLocale()
        cl.switch_locale(cl.Locale.RB)

    def _on_repeat_type_changed(self, repeat, repeat_type):
        if self.toggle_button.get_active():
            if repeat_type == RepeatPopContainer.ONE_SONG:
                self.repeat_song = True
            else:
                self.repeat_song = False
        else:
            self.repeat_song = False

        self._set_toggle_tooltip(repeat)

        print("repeat type changed", self.repeat_song)

    def on_gst_player_eos(self, gst_player, stream_data, early=0):
        """
        Set song_changed to SONG_CHANGED_EOS so that on_song_change will
        know to repeat the song.
        """
        if self.repeat_song:
            self.song_changed = self.SONG_CHANGED_EOS

    def on_song_change(self, player, time):
        """
        Repeat song that has just been played
        (when called on song change signal).
        """
        if self.song_changed == self.SONG_CHANGED_EOS:
            self.song_changed = self.SONG_CHANGED_MANUAL
            player.do_previous()

    # Since seg faults no longer seem to happen when the 'eos' callback
    # is called with GStreamer 1.0, on_gst_player_eos in conjunction
    # with on_song_change are used instead of this method to control the
    # song repetition. The related to GStreamer is described at
    # https://bugs.launchpad.net/ubuntu/+source/rhythmbox/+bug/1239218
    def on_elapsed_change(self, player, time):
        """
        This is a old method to 'repeat' the current song as soon as
        it reaches the last seconds.
        """
        if self.repeat_song:
            # This might be improved by keeping a instance variable with
            # the duration and updating it on_song_change in order to
            # avoid querying the duration on every call.
            duration = player.get_playing_song_duration()
            if duration > 0:
                # Repeat on the last two seconds of the song. Previously the
                # last second was used but RB now seems to use the last second
                # to prepare things for the next song of the list.
                if time >= duration - 2:
                    player.set_playing_time(0)


class RepeatPopContainer(Gtk.ButtonBox):
    __gsignals__ = {
        "repeat-type-changed": (GObject.SIGNAL_RUN_LAST, None, (int,))
    }

    # repeat-type-changed is emitted with one of the following values
    ONE_SONG = 1
    ALL_SONGS = 2

    def __init__(self, parent_container, parent_button, *args, **kwargs):
        super(RepeatPopContainer, self).__init__(*args, **kwargs)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_layout(Gtk.ButtonBoxStyle.START)
        self.props.margin = 5
        context = self.get_style_context()
        context.add_class('linked')

        icon_size = 4

        toggle1 = Gtk.RadioButton.new(None)
        toggle1.set_mode(False)
        fallback = 'media-playlist-repeat-symbolic'
        icon = Gio.ThemedIcon.new_with_default_fallbacks(fallback)
        image = Gtk.Image()
        image.set_from_gicon(icon, icon_size)
        image.props.margin = 5
        toggle1.set_image(image)
        toggle1.connect('leave-notify-event', self._on_popover_mouse_over)
        toggle1.connect('enter-notify-event', self._on_popover_mouse_over)
        toggle1.connect('toggled', self._on_popover_button_toggled)

        # locale stuff
        cl = CoverLocale()
        cl.switch_locale(cl.Locale.LOCALE_DOMAIN)

        if parent_button.get_has_tooltip():
            toggle1.set_tooltip_text(_("Repeat all tracks"))

        self._repeat_button = toggle1
        self.add(toggle1)
        self.child_set_property(toggle1, "non-homogeneous", True)
        toggle1.show_all()

        self._repeat_image = Gtk.Image()
        self._repeat_image.set_from_gicon(icon, icon_size)
        self._repeat_image.props.margin = 5

        toggle2 = Gtk.RadioButton.new_from_widget(toggle1)
        toggle2.set_mode(False)
        sym = 'media-playlist-repeat-song-symbolic'
        icon2 = Gio.ThemedIcon.new_with_default_fallbacks(sym)
        image2 = Gtk.Image()
        image2.set_from_gicon(icon2, icon_size)
        image2.props.margin = 5
        toggle2.set_image(image2)

        if parent_button.get_has_tooltip():
            toggle2.set_tooltip_text(_("Repeat the current track"))

        self._repeat_song_image = Gtk.Image()
        self._repeat_song_image.set_from_gicon(icon2, icon_size)
        self._repeat_song_image.props.margin = 5

        toggle2.connect('leave-notify-event', self._on_popover_mouse_over)
        toggle2.connect('enter-notify-event', self._on_popover_mouse_over)
        toggle2.connect('toggled', self._on_popover_button_toggled)
        toggle2.show_all()
        self._repeat_song_button = toggle2
        self.add(toggle2)
        self.child_set_property(toggle2, "non-homogeneous", True)

        self._popover_inprogress = 0
        parent_container.connect('leave-notify-event',
                                 self._on_popover_mouse_over)
        parent_container.connect('enter-notify-event',
                                 self._on_popover_mouse_over)
        parent_button.connect('leave-notify-event',
                              self._on_popover_mouse_over)
        parent_button.connect('enter-notify-event',
                              self._on_popover_mouse_over)

        parent_button.set_image(self._repeat_image)

        self._parent_container = parent_container
        self._parent_button = parent_button

        # now get the repeat-type saved in gsettings
        # get values from gsettings
        self.gs = GSetting()
        self.plugin_settings = self.gs.get_setting(self.gs.Path.PLUGIN)

        repeat_type = self.plugin_settings[self.gs.PluginKey.REPEAT_TYPE]

        if repeat_type == RepeatPopContainer.ONE_SONG:
            self._repeat_song_button.set_active(True)

    def _on_popover_button_toggled(self, button, *args):
        print("popover toggle")
        if button.get_active():
            if button == self._repeat_button:
                self._parent_button.set_image(self._repeat_image)
                self.emit('repeat-type-changed', RepeatPopContainer.ALL_SONGS)
                self.plugin_settings[self.gs.PluginKey.REPEAT_TYPE] = \
                    RepeatPopContainer.ALL_SONGS
            else:
                self._parent_button.set_image(self._repeat_song_image)
                self.emit('repeat-type-changed', RepeatPopContainer.ONE_SONG)
                self.plugin_settings[self.gs.PluginKey.REPEAT_TYPE] = \
                    RepeatPopContainer.ONE_SONG

    def get_repeat_type(self):
        repeat_type = RepeatPopContainer.ALL_SONGS
        if self._repeat_song_button.get_active():
            repeat_type = RepeatPopContainer.ONE_SONG

        return repeat_type

    def _on_popover_mouse_over(self, widget, eventcrossing):
        if eventcrossing.type == Gdk.EventType.ENTER_NOTIFY:
            if self._popover_inprogress == 0:
                self._popover_inprogress = 1
                print("enter1")
            else:
                self._popover_inprogress = 2
                print("enter2")
            self._popover_inprogress_count = 0

            if type(widget) is Gtk.ToggleButton:
                print("here")
                if widget.get_active():
                    print(self._parent_container)
                    self._parent_container.show_all()
        else:
            print("exit")
            self._popover_inprogress = 3

        def delayed(*args):
            if self._popover_inprogress == 3:
                self._popover_inprogress_count += 1

                if self._popover_inprogress_count < 5:
                    return True

                self._parent_container.hide()
                self._popover_inprogress = 0
                print("exit timeout")
                return False
            else:
                return True

        if self._popover_inprogress == 1:
            print("adding timeout")
            self._popover_inprogress = 2
            GLib.timeout_add(100, delayed)


class CustomPopover(Gtk.Window):
    def __init__(self, parent_button, *args, **kwargs):
        super(CustomPopover, self).__init__(type=Gtk.WindowType.POPUP, *args,
                                            **kwargs)

        self.set_decorated(False)
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.stick()
        self._parent_button = parent_button
        self.connect_after('show', self._on_show)
        # Track movements of the window to move calendar window as well
        self.connect("configure-event", self.on_window_config)

    def add(self, widget):
        self._frame = Gtk.Frame()
        self._frame.add(widget)

        super(CustomPopover, self).add(self._frame)
        self._frame.show_all()

    # Popoverwindow co ordinates without off-screen correction:
    #         Window origin (x, y)
    #          |
    #          V
    #          ---------------------------------
    #          | Main Window                   |
    #          |                               |
    #          |                               |
    #          |Toggle button's (x, y)         |
    #          |(relative to parent window)    |
    #          | |                             |
    #          | V                             |
    #          |  .........................    |
    # Popover  | |  Toggle Button          |   |
    # window's | |                         |   |
    # (x, y)---+> .........................    |
    #          |(window will be here) |
    #          |                               |
    #          |                               |
    #          ---------------------------------
    #   Popover Window's screen coordinates:
    #   x = Window's origin x + Toggle Button's relative x
    #   y = Window's origin y + Toggle Button's relative y + Toggle Button's
    #       height

    def _on_show(self, widget):
        rect = self._parent_button.get_allocation()
        main_window = self._parent_button.get_toplevel()
        [val, win_x, win_y] = main_window.get_window().get_origin()
        cal_x = win_x + rect.x
        cal_y = win_y + rect.y + rect.height

        [x, y] = self.apply_screen_coord_correction(cal_x, cal_y)
        self.move(x, y)

    # This function "tries" to correct calendar window position so that it is
    # not obscured when
    # a portion of main window is off-screen.
    # Known bug: If the main window is partially off-screen before Calendar
    # window
    # has been realized then get_allocation() will return rect of 1x1 in which
    # case
    # the calculations will fail & correction will not be applied
    def apply_screen_coord_correction(self, x, y):
        corrected_y = y
        corrected_x = x
        rect = self.get_allocation()
        screen_w = Gdk.Screen.width()
        screen_h = Gdk.Screen.height()

        delta_x = screen_w - (x + rect.width)
        delta_y = screen_h - (y + rect.height)
        if delta_x < 0:
            corrected_x += delta_x
            print("at x")
        if corrected_x < 0:
            corrected_x = 0

        button_rect = self._parent_button.get_allocation()
        window_width, window_height = \
            self._parent_button.get_toplevel().get_size()
        # print (y, button_rect.y, button_rect.height, )

        calc = (window_height - (button_rect.y + (button_rect.height * 2)))
        if delta_y < 0 or (calc < 0):
            btn_hgt = self._parent_button.get_allocation().height
            corrected_y = y - rect.height - btn_hgt
            print("at y")
        if corrected_y < 0:
            corrected_y = 0
        return [corrected_x, corrected_y]

    # "configure-event" callback of main window, try to move calendar window
    # along with main window.
    def on_window_config(self, widget, event):
        # Maybe better way to find the visiblilty
        if self.get_mapped():
            rect = self._parent_button.get_allocation()
            main_window = self._parent_button.get_toplevel()
            [val, win_x, win_y] = main_window.get_window().get_origin()
            cal_x = win_x + rect.x
            cal_y = win_y + rect.y + rect.height

            self.show_all()
            [x, y] = self.apply_screen_coord_correction(cal_x, cal_y)
            self.move(x, y)
