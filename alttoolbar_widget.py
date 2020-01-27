# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# alttoolbar_widget.py - custom widgets
# Copyright (C) 2015 - 2020 David Mohammed <fossfreedom@ubuntu.com>
# Copyright (C) 2018 Nguyễn Gia Phong <vn.mcsinyx@gmail.com>
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


class Slider(Gtk.Scale):
    """Wrapper around Gtk.Scale to handle signals from user and
    Rhythmbox itself.
    """

    def __init__(self, shell_player):
        super().__init__()
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.adjustment = Gtk.Adjustment(0, 0, 10, 1, 10, 0)
        self.set_adjustment(self.adjustment)
        self.set_hexpand(True)
        self.set_draw_value(False)
        self.set_sensitive(False)

        self.shell_player = shell_player
        self.dragging = self.drag_moved = False

        self.connect('button-press-event', slider_press_callback)
        self.connect('motion-notify-event', slider_moved_callback)
        self.connect('button-release-event', slider_release_callback)
        self.connect('focus-out-event', slider_release_callback)
        self.changed_callback_id = self.connect('value-changed',
                                                slider_changed_callback)

        self.set_size_request(150, -1)
        self.show_all()

    def apply_position(self):
        """Sync slider elapsed time with Rhythmbox."""
        self.shell_player.set_playing_time(self.adjustment.get_value())


def slider_press_callback(slider, event):
    """Handle 'button-press-event' signals."""
    slider.dragging = True
    slider.drag_moved = False
    return False


def slider_moved_callback(slider, event):
    """Handle 'motion-notify-event' signals."""
    if not slider.dragging:
        return False
    slider.drag_moved = True
    slider.apply_position()
    return False


def slider_release_callback(slider, event):
    """Handle 'button-release-event' and 'focus-out-event' signals."""
    if not slider.dragging:
        return False
    if slider.drag_moved:
        slider.apply_position()
    slider.dragging = slider.drag_moved = False
    return False


def slider_changed_callback(slider):
    """Handle 'value-changed-event' signals."""
    slider.apply_position()
