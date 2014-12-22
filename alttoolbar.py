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
from gi.repository import Peas

from alttoolbar_rb3compat import ActionGroup
from alttoolbar_rb3compat import ApplicationShell

view_menu_ui = """
<ui>
  <menubar name="MenuBar">
    <menu name="ViewMenu" action="View">
      <menuitem name="Show Toolbar" action="ToggleToolbar" />
    </menu>
  </menubar>
</ui>
"""

class AltToolbarPlugin(GObject.Object, Peas.Activatable):
    '''
    Main class of the plugin. Manages the activation and deactivation of the
    plugin.
    '''
    __gtype_name = 'AltToolbarPlugin'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        '''
        Initialises the plugin object.
        '''
        GObject.Object.__init__(self)

    def do_activate(self):
        '''
        Called by Rhythmbox when the plugin is activated. It creates the
        plugin's source and connects signals to manage the plugin's
        preferences.
        '''

        self.shell = self.object
        self.db = self.shell.props.db


        self.appshell = ApplicationShell(self.shell)
        self.toggle_action_group = ActionGroup(self.shell, 'AltToolbarPluginActions')
        self.toggle_action_group.add_action(func=self.toggle_visibility,
        action_name='ToggleToolbar', label=_("Show Toolbar"), action_state=ActionGroup.TOGGLE,
        action_type='app', accel="<Ctrl>t", tooltip=_("Show or hide the main toolbar"))
        self.appshell.insert_action_group(self.toggle_action_group)
        self.appshell.add_app_menuitems(view_menu_ui, 'AltToolbarPluginActions', 'view')

        self.rb_toolbar = self.find(self.shell.props.window,
                                   'main-toolbar', 'by_id')
        
        self.rb_toolbar.hide()                          

    # Couldn't find better way to find widgets than loop through them
    def find(self, node, search_id, search_type):
        print (node.get_name())
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
        self.appshell.cleanup()
        self.rb_toolbar.set_visible(True)
        del self.shell
        del self.db
        
    def toggle_visibility(self, action, param=None, data=None):
        action = self.toggle_action_group.get_action('ToggleToolbar')

        self.rb_toolbar.set_visible(action.get_active())
