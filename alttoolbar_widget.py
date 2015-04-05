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

import math

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject


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

        self.set_hexpand(True)
        self.props.height_request = 5
        self.props.margin_bottom = 2

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
        '''
                    <child>
                      <object class="alternative-toolbar+SmallProgressBar" id="song progress">
                        <property name="height-request">5</property>
                        <property name="margin-bottom">2</property>
                        <signal name="control" handler="progress_control"/>
                      </object>
                      <packing>
                        <property name="expand">True</property>
                        <property name="fill">True</property>
                        <property name="position">1</property>
                      </packing>
                    </child>
                    
        '''


class SmallScale(Gtk.Scale):
    __gsignals__ = {
        'control': (GObject.SIGNAL_RUN_LAST, None, (float,))
    }

    def __init__(self):
        super(SmallScale, self).__init__()
        self.__progress__ = 0

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self._adjustment = Gtk.Adjustment(0, 0, 1, 0.01, 0.1, 0)
        self.set_adjustment(self._adjustment)
        self.set_hexpand(True)
        self.set_draw_value(False)

        self.button_pressed = False
        self.button_time = 0

        self.connect('button-press-event', self._button_press_event)
        self.connect('button-release-event', self._button_release_event)
        self.connect('motion-notify-event', self._motion_notify_event)

    @GObject.Property
    def progress(self):
        return self.__progress__

    @progress.setter
    def progress(self, value):
        self.__progress__ = value
        self.set_value(value)

    def _motion_notify_event(self, widget, event):
        if ( self.button_pressed ):
            self.control_by_event(event)
            return True
        else:
            return False

    def _button_press_event(self, widget, event):
        self.button_pressed = True
        self.control_by_event(event)
        return False

    def _button_release_event(self, widget, event):
        self.button_pressed = False
        self.control_by_event(event)
        return False

    def control_by_event(self, event):
        if ( self.button_time + 100 < event.time ):
            allocw = self.get_allocated_width()
            fraction = event.x / allocw
            self.button_time = event.time
            self.emit("control", fraction)
