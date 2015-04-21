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
from gi.repository import GdkPixbuf
from gi.repository import Gio

import rb

class AltControllerCategory(object):
    OTHER = 0
    LOCAL = 1
    ONLINE = 2
    PLAYLIST = 3

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

        self._pixbuf = None

        super(AltControllerBase, self).__init__()
        
    def get_category(self):
        ''' 
           return the category type for the source
        '''
        
        return AltControllerCategory.OTHER

    def _get_pixbuf(self, filename):
        filename = rb.find_plugin_file(self.header.plugin, filename)
        what, width, height = Gtk.icon_size_lookup(Gtk.IconSize.BUTTON)

        self._pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename, 128, 128)

        if self._pixbuf.get_width() != width or self._pixbuf.get_height() != height:
            self._pixbuf = pixbuf.scale_simple(16, 16,
                                         GdkPixbuf.InterpType.BILINEAR)

        return self._pixbuf

    def get_icon_pixbuf(self, source):
        '''
          return the pixbuf for the source
        :param plugin
        :param source:
        :return:
        '''
        self._pixbuf = None
        if source.props.icon:
            try:
                names = source.props.icon.props.names

                default = Gtk.IconTheme.get_default()
                info = default.choose_icon(names, 16, 0)
                style_context = source.get_style_context()
                self._pixbuf, symbol = info.load_symbolic_for_context(style_context)
            except:
                filename = source.props.icon.get_file().get_path()
                return self._get_pixbuf(filename)

        return self._pixbuf

    def get_gicon(self, source):
        '''
          return the source icon
        :param source:
        :return:
        '''

        if source.props.icon:
            return source.props.icon

        return None

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
        for child in container.get_children():
            container.remove(child)

    def hide_controls(self, source):
        '''
          hide controls for a given controller
        '''

        pass

    def get_search_entry(self, toolbar_container):
        '''
          find the GtkEntry field corresponding to the search entry
          
          returns 1. the GtkWidget containing the GtkEntry 
                  2. the GtkEntry 
                  
          returns None if nothing found
          
        '''

        return None

    def get_toolbar(self, source):
        '''
          return GtkWidget corresponding to the toolbar within the source
                 None if no toolbar
        '''

        return None

    def moveto_searchbar(self, toolbar, widget, searchbar):
        '''
          move from toolbar the widget and add to the searchbar
        '''

        pass

class AltGenericController(AltControllerBase):
    '''
    generic controller for the headerbar (only)
    '''
    __gtype_name = 'AltGenericController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltGenericController, self).__init__(header)

        self.centre_controls = {}
        self.end_controls = {}
        
    def get_category(self):
        return AltControllerCategory.LOCAL

    def hide_controls(self, source):
        val, view_button = self.header.has_button_with_label(source, _('View All'))

        if val:
            view_button.set_visible(False)

    def get_toolbar(self, source):

        toolbar = self.find(source, 'RBSourceToolbar', 'by_name')
        print(toolbar)
        print(source)

        return toolbar

    def get_search_entry(self, container):
        if container == None:
            print ("no container to search")
            return None, None
        search = self.find(container, 'RBSearchEntry', 'by_name')

        if not search:
            print("no RBSearchEntry found")
            return None, None

        entry = self.find(search, 'GtkEntry', 'by_name')
        print(entry)
        return search, entry

    def moveto_searchbar(self, toolbar, search, searchbar):
        toolbar.remove(search)
        toolbar.set_visible(False)

        searchbar.add(search)

    def update_controls(self, source):
        '''
           update the button controls on the header
        '''

        val, browser_button = self.header.is_browser_view(source)
        if not val:
            # if not a browser_view based source then default just to the title
            print("no browser view")
            self.header.set_library_box_sensitive(False)
        else:
            print("browser view found")
            browser_button.set_visible(False)
            self.header.set_library_box_sensitive(True)

        self.header.current_search_button = None
        
        toolbar = self.get_toolbar(source)
        if not toolbar:
            # there is no source-bar so the header is empty
            print("no toolbar so nothing left to do - cleanup endbox and exit")
            self.remove_controls(self.header.end_box)
            return

        self.hide_controls(toolbar)

        if source not in self.end_controls:
            # this is the first time for the source so extract the RBSearchEntry
            print("first time around")
            controls = {}

            self.remove_controls(self.header.end_box)

            print (toolbar)
            search, entry = self.get_search_entry(toolbar)
            if not search:
                return

            if self.header.searchbar:
                self.header.searchbar.set_visible(False)

            # define a searchbar widget
            self.header.searchbar = Gtk.SearchBar.new()
            #self.header.shell.add_widget(self.header.searchbar,
            #                             RB.ShellUILocation.MAIN_TOP, expand=False, fill=False)

            # we need to add this to the top of the source window
            # todo this - find the first child and physically move this into the
            # second position in a box - the first position being the searchbar
            children = source.get_children()
            print (children)
            first = children[0]
            box = Gtk.Box()
            box.set_orientation(Gtk.Orientation.VERTICAL)
            box.pack_start(self.header.searchbar, False, True, 0)
            box.show_all()
            Gtk.Container.remove(source, first)
            box.pack_start(first, True, True, 1)
            
            source.add(box)
            
            self.moveto_searchbar(toolbar, search, self.header.searchbar)
            self.header.searchbar.connect_entry(entry)
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
            self.header.current_search_button = search_button
            self.end_controls[source] = controls
            print(controls)
        else:
            print("second time around")
            print(self.end_controls[source])
            search = self.end_controls[source]['searchbar']
            if self.header.searchbar:
                self.header.searchbar.set_visible(False)
            self.header.searchbar = search
            self.header.searchbar.set_visible(True)

            self.remove_controls(self.header.end_box)
            search_button = self.end_controls[source]['search_button']
            self.header.current_search_button = search_button
            self.header.end_box.add(search_button)
            self.header.end_box.reorder_child(search_button, 0)
            self.header.end_box.show_all()


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


class AltSoundCloudController(AltGenericController):
    '''
    sound-cloud controller
    '''
    __gtype_name = 'AltSoundCloudController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltSoundCloudController, self).__init__(header)

        self._has_toolbar = None

    def valid_source(self, source):
        '''
          override
        '''

        return "SoundCloud" in type(source).__name__
        
    def get_category(self):
        return AltControllerCategory.ONLINE

    def get_toolbar(self, source):
        if self._has_toolbar:
            return self._has_toolbar

        search_box = self.find(source, 'box1', 'by_id')

        self._has_toolbar = search_box
        return search_box

    def moveto_searchbar(self, toolbar, widget, searchbar):
        '''
          override - here we want to actually remove the toolbar from the source
          so get the parent
        '''

        parent_grid = toolbar.get_parent()
        parent_grid.remove(toolbar)
        searchbar.add(toolbar)


class AltCoverArtBrowserController(AltGenericController):
    '''
    sound-cloud controller
    '''
    __gtype_name = 'AltCoverArtBrowserController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltCoverArtBrowserController, self).__init__(header)

        self._has_toolbar = None

    def valid_source(self, source):
        '''
          override
        '''

        return "CoverArtBrowser" in type(source).__name__
        
    def get_category(self):
        return AltControllerCategory.LOCAL

    def get_toolbar(self, source):
        if self._has_toolbar:
            return self._has_toolbar

        search_box = self.find(source, 'toolbar', 'by_id')

        self._has_toolbar = search_box
        return search_box

    def moveto_searchbar(self, toolbar, widget, searchbar):
        '''
          override - here we want to actually remove the toolbar from the source
          so get the parent
        '''

        parent_grid = toolbar.get_parent()
        parent_grid.remove(toolbar)
        searchbar.add(toolbar)

    def get_search_entry(self, toolbar):
        '''
          override - use the GtkEntry in the coverartbrowser
        '''

        entrysearch = self.find(toolbar, 'entry_search_alignment', 'by_id')
        entry = self.find(entrysearch, 'GtkEntry', 'by_name')

        return entrysearch, entry

class AltQueueController(AltGenericController):
    '''
    RB QueueSource controller
    '''
    __gtype_name = 'AltQueueController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltQueueController, self).__init__(header)

        self._gicon = Gio.ThemedIcon(name='audio-x-queue-symbolic')

    def valid_source(self, source):
        return "RBPlayQueueSource" in type(source).__name__

    def get_gicon(self, source):
        return self._gicon


class AltErrorsController(AltGenericController):
    '''
    RB ErrorsSource controller
    '''
    __gtype_name = 'AltErrorsController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltErrorsController, self).__init__(header)

        self._gicon = Gio.ThemedIcon(name='dialog-error-symbolic')

    def valid_source(self, source):
        return "RBImportErrorsSource" in type(source).__name__

    def get_category(self):
        return AltControllerCategory.LOCAL

    def get_gicon(self, source):
        return self._gicon

        
class AltRadioController(AltGenericController):
    '''
    RB RadioSource controller
    '''
    __gtype_name = 'AltRadioController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltRadioController, self).__init__(header)

        self._gicon = Gio.ThemedIcon(name='audio-radio-symbolic')

    def valid_source(self, source):
        return "RBIRadioSource" in type(source).__name__

    def get_gicon(self, source):
        return self._gicon
        
    def get_category(self):
        return AltControllerCategory.ONLINE
        
class AltLastFMController(AltGenericController):
    '''
    RB LastFMSource controller
    '''
    __gtype_name = 'AltLastFMController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltLastFMController, self).__init__(header)

        self._libre_gicon = Gio.ThemedIcon(name='librefm-symbolic')
        self._lastfm_gicon = Gio.ThemedIcon(name='lastfm-symbolic')

    def valid_source(self, source):
        return "RBAudioscrobblerProfilePage" in type(source).__name__

    def get_gicon(self, source):
        if source.props.name == _("Libre.fm"):
            return self._libre_gicon
        else:
            return self._lastfm_gicon
        
    def get_category(self):
        return AltControllerCategory.ONLINE

class AltPlaylistController(AltGenericController):
    '''
    playlist controller
    '''
    __gtype_name = 'AltPlaylistController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltPlaylistController, self).__init__(header)

        self._static_gicon = Gio.ThemedIcon(name='audio-x-playlist-symbolic')
        self._auto_gicon = Gio.ThemedIcon(name='audio-x-playlist-automatic-symbolic')

        self._toprated_gicon = Gio.ThemedIcon(name='starred-symbolic')
        self._recentlyadded_gicon = Gio.ThemedIcon(name='audio-x-playlist-recently-added-symbolic')
        self._recentlyplayed_gicon = Gio.ThemedIcon(name='audio-x-playlist-recently-played-symbolic')


    def valid_source(self, source):
        '''
          override
        '''
        return "PlaylistSource" in type(source).__name__

    def get_gicon(self, source):

        if source.props.name == _('My Top Rated'):
            return self._toprated_gicon

        if source.props.name == _('Recently Added'):
            return self._recentlyadded_gicon

        if source.props.name == _('Recently Played'):
            return self._recentlyplayed_gicon

        if "StaticPlaylistSource" in type(source).__name__:
            return self._static_gicon
        else:
            return self._auto_gicon

    def get_category(self):
        return AltControllerCategory.PLAYLIST


class AltStandardOnlineController(AltGenericController):
    '''
      standard controller where we dont need specific customisation
    '''
    __gtype_name = 'AltStandardOnlineController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltStandardOnlineController, self).__init__(header)

        self._source_types=[ 'RBPodcastMainSource',
                             'MagnatuneSource',
                             'RBGriloSource',
                             'RadioBrowserSource']

    def valid_source(self, source):

        print (type(source).__name__)
        for source_type in self._source_types:
            if source_type in type(source).__name__:
                return True

        return False

    def get_category(self):
        return AltControllerCategory.ONLINE

class AltStandardLocalController(AltGenericController):
    '''
      standard controller where we dont need specific customisation
    '''
    __gtype_name = 'AltStandardLocalController'

    def __init__(self, header):
        '''
        Initialises the object.
        '''
        super(AltStandardLocalController, self).__init__(header)

        self._source_types=[ 'RBMtpSource',
                             'RBMissingFilesSource']

    def valid_source(self, source):

        print (type(source).__name__)
        for source_type in self._source_types:
            if source_type in type(source).__name__:
                return True

        return False

    def get_category(self):
        return AltControllerCategory.LOCAL
