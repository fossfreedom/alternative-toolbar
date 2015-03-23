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

from datetime import datetime, date

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Peas
from gi.repository import PeasGtk
from gi.repository import RB
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import Gio

from alttoolbar_rb3compat import gtk_version
from alttoolbar_rb3compat import ActionGroup
from alttoolbar_rb3compat import ApplicationShell
import rb
import math

class AltToolbarBase(GObject.Object):
    '''
    base for all toolbar types - never instantiated by itself
    '''

    def __init__(self):
        '''
        Initialises the object.
        '''
        GObject.Object.__init__(self)
        
class AltToolbarStandard(AltToolbarBase):
    '''
    standard RB toolbar
    '''
    __gtype_name = 'AltToolbarStandard'

    def __init__(self):
        '''
        Initialises the object.
        '''
        AltToolbarBase.__init__(self)
        
class AltToolbarShared(AltToolbarBase):
    '''
    shared components for the compact and headerbar toolbar types
    '''

    def __init__(self):
        '''
        Initialises the object.
        '''
        AltToolbarBase.__init__(self)
        
class AltToolbarCompact(AltToolbarShared):
    '''
    compact RB toolbar
    '''
    __gtype_name = 'AltToolbarCompact'

    def __init__(self):
        '''
        Initialises the object.
        '''
        AltToolbarShared.__init__(self)
        
class AltToolbarHeaderBar(AltToolbarShared):
    '''
    headerbar RB toolbar
    '''
    __gtype_name = 'AltToolbarHeaderBar'

    def __init__(self):
        '''
        Initialises the object.
        '''
        AltToolbarShared.__init__(self)
        
