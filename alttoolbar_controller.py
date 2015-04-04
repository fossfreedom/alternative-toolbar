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

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import RB
from gi.repository import GLib

import rb


class AltControllerBase(GObject.Object):
    '''
    base controller
    '''

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        self.header = header
        self.find = self.header.find  # convenience function

        super(AltControllerBase, self).__init__()

    def valid_source(self, source):
        '''
          returns bool if the given source is applicable to the controller
        '''

        return False

    def update_controls(self, source):
        '''
           update the button controls on the header
        '''

        pass

    def remove_controls(self, container):
        '''
          remove any controls that are contained in a container
        '''
        print("remove_controls")
        for child in container.get_children():
            print(child)
            container.remove(child)

    def hide_controls(self, source):
        '''
          hide controls for a given controller
        '''

        pass

class AltExampleController(AltControllerBase):
    '''
    example controller
    '''
    __gtype_name = 'AltExampleController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltExampleController, self).__init__(header)

    def valid_source(self, source):
        '''
          override
        '''

        a_bool_result = "RBPodcastMainSource" in type(source).__name__

        #return "RBIRadioSource" in type(ource).__name__:

        # so we should pass the page to our object.is_of_type() and this will return true/false 

        # from coverart_browser_source import CoverArtBrowserSource
        #if isinstance(page, CoverArtBrowserSource):
        #    print ("is coverart")

        #from MagnatuneSource import MagnatuneSource
        #if isinstance(page, MagnatuneSource):
        #    print ("is magnatune")

        # RBMissingFilesSource
        # is playlist if page is in this
        #print (self.shell.props.playlist_manager.get_playlists())
        #if page in self.shell.props.playlist_manager.get_playlists():
        #    print("true playlist")
        #else:
        #    print("not playlist")

        return a_bool_result


class AltGenericController(AltControllerBase):
    '''
    base controller
    '''
    __gtype_name = 'AltGenericController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltGenericController, self).__init__(header)
        print ("###")
        self.centre_controls = {}
        self.end_controls = {}

        builder = Gtk.Builder()
        ui = rb.find_plugin_file(self.header.plugin, 'ui/altlibrary.ui')
        builder.add_from_file(ui)

        self.header.load_builder_content(builder)

        view_name = "Categories"
        self.header.library_browser_radiobutton.set_label(view_name)

        self.header.library_browser_radiobutton.connect('toggled', self.header.library_radiobutton_toggled)
        self.header.library_song_radiobutton.connect('toggled', self.header.library_radiobutton_toggled)

    def hide_controls(self, source):
        val, view_button = self.header.has_button_with_label(source, _('View All'))
        
        if val:
            view_button.set_visible(False)
        
    def update_controls(self, source):
        '''
           update the button controls on the header
        '''

        toolbar = self.find(source, 'RBSourceToolbar', 'by_name')
        print(toolbar)
        print(source)

        val, browser_button = self.header.is_browser_view(source)
        if not val:
            # if not a browser_view based source then default just to the title
            print("no browser view")
            label = Gtk.Label.new()
            markup = "<b>{title}</b>".format(
                title=GLib.markup_escape_text(_("Rhythmbox")))
            label.set_markup(markup)
            label.show_all()

            self.header.headerbar.set_custom_title(label)
        else:
            # self.library_search_togglebutton.connect('toggled', self._sh_on_toolbar_btn_clicked)
            print("browser view found")
            browser_button.set_visible(False)
            self.header.headerbar.set_custom_title(self.header.library_box)

        if not toolbar:
            # there is no source-bar so the header is empty
            self.remove_controls(self.header.end_box)
            return
            
        self.hide_controls(toolbar)

        if source not in self.end_controls:
            # this is the first time for the source so extract the RBSearchEntry
            print("first time around")
            search = self.find(toolbar, 'RBSearchEntry', 'by_name')

            self.remove_controls(self.header.end_box)

            if not search:
                print("no RBSearchEntry found")
                return

            controls = {}

            entry = self.find(search, 'GtkEntry', 'by_name')
            print(entry)
            toolbar.remove(search)
            toolbar.set_visible(False)

            print("removing from searchbar")
            # self.remove_controls(self.header.searchbar)
            if self.header.searchbar:
                self.header.searchbar.set_visible(False)
            # define a searchbar widget
            self.header.searchbar = Gtk.SearchBar.new()
            self.header.searchbar.show_all()
            self.header.shell.add_widget(self.header.searchbar,
                                         RB.ShellUILocation.MAIN_TOP, expand=False, fill=False)

            self.header.searchbar.add(search)
            self.header.searchbar.show_all()

            search_button = Gtk.ToggleButton.new()
            image = Gtk.Image.new_from_icon_name("preferences-system-search-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
            search_button.add(image)

            self.header.end_box.add(search_button)
            self.header.end_box.reorder_child(search_button, 0)
            search_button.show_all()
            search_button.connect('toggled', self.header.search_button_toggled)

            controls['searchbar'] = self.header.searchbar
            controls['search_button'] = search_button
            self.end_controls[source] = controls
            print(search_button)
        else:
            print("second time around")
            search = self.end_controls[source]['searchbar']
            if self.header.searchbar:
                self.header.searchbar.set_visible(False)
            self.header.searchbar = search
            self.header.searchbar.set_visible(True)

            self.remove_controls(self.header.end_box)
            search_button = self.end_controls[source]['search_button']
            self.header.end_box.add(search_button)
            self.header.end_box.reorder_child(search_button, 0)
            search_button.show_all()
            

class AltMusicLibraryController(AltGenericController):
    '''
    music library controller
    '''
    __gtype_name = 'AltMusicLibraryController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltMusicLibraryController, self).__init__(header)

    def valid_source(self, source):
        '''
          override
        '''

        return "LibrarySource" in type(source).__name__
            
    def hide_controls(self, source):
        super(AltMusicLibraryController, self).hide_controls(source)
        
        val, import_button = self.header.has_button_with_label(source, _('Import'))
        
        if val:
            import_button.set_visible(False)
