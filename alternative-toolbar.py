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
from gi.repository import RB
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GdkPixbuf

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

class AltToolbarPlugin(GObject.Object, Peas.Activatable):
    '''
    Main class of the plugin. Manages the activation and deactivation of the
    plugin.
    '''
    __gtype_name = 'AltToolbarPlugin'
    object = GObject.property(type=GObject.Object)
    
    # Builder releated utility functions... ####################################
    
    def load_builder_content(self, builder):
        if( not hasattr( self, "__builder_obj_names" ) ):
            self.__builder_obj_names = list()
    
        for obj in builder.get_objects():
            if( isinstance( obj, Gtk.Buildable ) ):
                name = Gtk.Buildable.get_name(obj).replace(' ', '_')
                self.__dict__[ name ] = obj
                self.__builder_obj_names.append( name )

    def connect_builder_content( self, builder ):
        builder.connect_signals_full( self.connect_builder_content_func, self )

    def connect_builder_content_func( self,
                                      builder,
                                      object,
                                      sig_name,
                                      handler_name,
                                      conn_object,
                                      flags,
                                      target ):
        handler = None
        
        h_name_internal = "_sh_" + handler_name.replace(" ", "_")
    
        if( hasattr( target, h_name_internal ) ):
            handler = getattr( target, h_name_internal )
        else:
            handler = eval(handler_name)
        
        object.connect( sig_name, handler )

    def purge_builder_content( self ):
        for name in self.__builder_obj_names:
            o = self.__dict__[ name ]
            if( isinstance( o, Gtk.Widget ) ):
                o.destroy()
            del self.__dict__[ name ]
    
        del self.__builder_obj_names
    

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
        self.main_window = self.shell.props.window
        self.main_window.set_border_width(10)
        
        # Prepare internal variables
        self.song_duration = 0
        self.cover_pixbuf = None
        self.entry = None
        
        # Prepare Album Art Displaying
        self.album_art_db = GObject.new( RB.ExtDB, name="album-art" )
        

        #self.main_window.set_decorated(False)

        self.appshell = ApplicationShell(self.shell)
        self.toggle_action_group = ActionGroup(self.shell, 'AltToolbarPluginActions')
        self.toggle_action_group.add_action(func=self.toggle_visibility,
        action_name='ToggleToolbar', label=_("Show Toolbar"), action_state=ActionGroup.TOGGLE,
        action_type='app', accel="<Ctrl>t", tooltip=_("Show or hide the main toolbar"))
        self.appshell.insert_action_group(self.toggle_action_group)
        self.appshell.add_app_menuitems(view_menu_ui, 'AltToolbarPluginActions', 'view')

        self.rb_toolbar = self.find(self.shell.props.window,
                                   'main-toolbar', 'by_id')
                                   
        builder = Gtk.Builder()
        ui = rb.find_plugin_file(self, 'ui/alttoolbar.ui')
        print (ui)
        builder.add_from_file( ui )
        
        self.load_builder_content( builder )
        self.connect_builder_content( builder )
        
        # Bring Builtin Actions to plugin
        for (a, b) in ((self.play_button, "play"),
                       (self.prev_button, "play-previous"),
                       (self.next_button, "play-next"),
                       (self.repeat_toggle, "play-repeat"),
                       (self.shuffle_toggle, "play-shuffle")):
            a.set_action_name("app." + b)
            #if b == "play-repeat" or b == "play-shuffle":
            #    a.set_action_target_value(GLib.Variant("b", True))
    
        self.headerbar = Gtk.HeaderBar.new()   
        #self.headerbar.set_title("Rhythmbox")
        self.headerbar.set_show_close_button(True)
        self.headerbar.pack_start(self.small_bar)
        self.headerbar.show_all()

        #self.shell.add_widget(self.headerbar,
        #    RB.ShellUILocation.MAIN_TOP, expand=True, fill=True)
        self.main_window.set_titlebar(self.headerbar) # this is needed for gnome-shell to replace the decoration
        self.rb_toolbar.hide()   
        
        # Connect signal handlers to rhythmbox
        self.shell_player = self.shell.props.shell_player
        self.sh_psc = self.shell_player.connect("playing-song-changed",
                                                self._sh_on_song_change )
        
        self.sh_op = self.shell_player.connect("elapsed-changed",
                                                self._sh_on_playing )  
        
        
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
        self.shell_player.disconnect( self.sh_op )
        self.shell_player.disconnect( self.sh_psc )
        del self.shell_player
        
        self.appshell.cleanup()
        self.rb_toolbar.set_visible(True)
        
        self.purge_builder_content()
        del self.shell
        del self.db
        
    def toggle_visibility(self, action, param=None, data=None):
        action = self.toggle_action_group.get_action('ToggleToolbar')

        self.rb_toolbar.set_visible(action.get_active())
        
    def display_song(self, entry):
        self.entry = entry
        
        self.cover_pixbuf = None
        self.album_cover.clear()
        
        if( entry is None ):
            self.song_button_label.set_text( "" )
        
        else:
            self.song_button_label.set_markup(
                "<b>{title}</b> <small>{album} - {artist}</small>".format(
                title = entry.get_string( RB.RhythmDBPropType.TITLE ),
                album = entry.get_string( RB.RhythmDBPropType.ALBUM ),
                artist = entry.get_string( RB.RhythmDBPropType.ARTIST ) ) )
                
            print (self.song_button_label.get_label())
            
            key = entry.create_ext_db_key( RB.RhythmDBPropType.ALBUM )
            self.album_art_db.request( key,
                                       self.display_song_album_art_callback,
                                       entry )
                                       
    def display_song_album_art_callback( self, key, filename, data, entry ):
        if( ( data is not None ) and ( isinstance( data, GdkPixbuf.Pixbuf ) ) ):
            self.cover_pixbuf = data
            scale_cover = self.cover_pixbuf.scale_simple( 24, 24,
                                                          GdkPixbuf.InterpType.HYPER )
            
            self.album_cover.set_from_pixbuf( scale_cover )
        else:
            self.cover_pixbuf = None
            self.album_cover.clear()
                                       
    # Signal Handlers ##########################################################
    
    def _sh_on_song_change(self, player, entry):
        if( entry is not None ):
            self.song_duration = entry.get_ulong( RB.RhythmDBPropType.DURATION )
        else:
            self.song_duration = 0
        self.display_song(entry)
    
    def _sh_on_playing(self, player, second ):
        if( self.song_duration != 0 ):
            self.song_progress.progress = float(second) / self.song_duration
        
    def _sh_progress_control( self, progress, fraction ):
        if( self.song_duration != 0 ):
            self.shell_player.set_playing_time( self.song_duration * fraction )
    
    def _sh_bigger_cover( self, cover, x, y, key, tooltip ):
        if( self.cover_pixbuf is not None ):
            tooltip.set_icon( self.cover_pixbuf.scale_simple( 300, 300,
                                                          GdkPixbuf.InterpType.HYPER ) )
            return True
        else:
            return False

        
################################################################################
# Custom Widgets ###############################################################

class SmallProgressBar( Gtk.DrawingArea ):
    
    __gsignals__ = {
        "control": (GObject.SIGNAL_RUN_LAST, None, (float,))
    }
    
    @GObject.Property
    def progress( self ):
        return self.__progress__
    
    @progress.setter
    def progress( self, value ):
        self.__progress__ = value
        self.queue_draw()
    
    def __init__( self ):
        super( SmallProgressBar, self).__init__()
        self.add_events( Gdk.EventMask.POINTER_MOTION_MASK |
                         Gdk.EventMask.BUTTON_PRESS_MASK |
                         Gdk.EventMask.BUTTON_RELEASE_MASK )
        self.button_pressed = False
        self.button_time = 0
        self.__progress__ = 0
    
    def do_draw( self, cc ):
        alloc = self.get_allocation()
        sc = self.get_style_context()
        fgc = sc.get_color( self.get_state_flags() )
        
        cc.set_source_rgba(1, 1, 1, 1 )
        cc.rectangle(0, 0, alloc.width, alloc.height )
        cc.fill()
        
        cc.set_source_rgba( fgc.red, fgc.green, fgc.blue, fgc.alpha )
        cc.rectangle(0, 0, alloc.width * self.progress, alloc.height )
        cc.fill()
        
    def do_motion_notify_event( self, event ):
        if( self.button_pressed ):
            self.control_by_event( event )
            return True
        else:
            return False
    
    def do_button_press_event( self, event ):
        self.button_pressed = True
        self.control_by_event( event )
        return True
    
    def do_button_release_event( self, event ):
        self.button_pressed = False
        self.control_by_event( event )
        return True
    
    def control_by_event( self, event ):
        allocw = self.get_allocated_width()
        fraction = event.x / allocw
        if( self.button_time + 100 < event.time ):
            self.button_time = event.time
            self.emit( "control", fraction )

