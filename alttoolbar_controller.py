# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright (C) 2015 - 2020 David Mohammed <fossfreedom@ubuntu.com>
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

from alttoolbar_preferences import CoverLocale
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import Gtk


class AltControllerCategory(object):
    OTHER = 0
    LOCAL = 1
    ONLINE = 2
    PLAYLIST = 3


class AltControllerBase(GObject.Object):
    """
    base controller
    """

    def __init__(self, header):
        """
        Initialises the object.
        """
        self.header = header
        self.find = self.header.find  # convenience function

        self._pixbuf = None

        super(AltControllerBase, self).__init__()

    def get_category(self):
        """
           return the category type for the source
        """

        return AltControllerCategory.OTHER

    def toolbar_visibility(self):
        """
            return the toolbar visibility
              by default None which means user controlled
        """

        return None

    def get_gicon(self, source):
        """
          return the source icon
        :param source:
        :return:
        """

        if source.props.icon:
            return source.props.icon

        return None

    def valid_source(self, source):
        """
          returns bool if the given source is applicable to the controller
        """

        return False

    def update_controls(self, source):
        """
           update the button controls on the header
        """

        pass

    def remove_controls(self, container):
        """
          remove any controls that are contained in a container
        """
        for child in container.get_children():
            container.remove(child)

    def hide_controls(self, source):
        """
          hide controls for a given controller
        """

        pass

    def get_search_entry(self, toolbar_container):
        """
          find the GtkEntry field corresponding to the search entry
          returns 1. the GtkWidget containing the GtkEntry
                  2. the GtkEntry
          returns None if nothing found
        """

        return None

    def get_toolbar(self, source):
        """
          return GtkWidget corresponding to the toolbar within the source
                 None if no toolbar
        """

        return None

    def moveto_searchbar(self, toolbar, widget, searchbar):
        """
          move from toolbar the widget and add to the searchbar
        """

        pass

    def set_library_labels(self):
        """
          set the centre library song-category button label
        """

        self.header.set_library_labels()


class AltGenericController(AltControllerBase):
    """
    generic controller for the headerbar (only)
    """
    __gtype_name = 'AltGenericController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltGenericController, self).__init__(header)

        self.centre_controls = {}
        self.end_controls = {}

    def get_category(self):
        return AltControllerCategory.LOCAL

    def hide_controls(self, source):
        val, view_button = self.header.has_button_with_label(source,
                                                             _('View All'))

        if val:
            view_button.set_visible(False)

    def get_toolbar(self, source):

        toolbar = self.find(source, 'RBSourceToolbar', 'by_name')
        print(toolbar)
        print(source)

        return toolbar

    def get_search_entry(self, container):
        if container is None:
            print("no container to search")
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
        """
           update the button controls on the header
        """

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
            # this is the first time for the source so extract the
            # RBSearchEntry
            print("first time around")
            controls = {}

            self.remove_controls(self.header.end_box)

            print(toolbar)  # should be the RBSourceToolbar
            search, entry = self.get_search_entry(toolbar)
            if not search:
                return

            if self.header.searchbar:
                self.header.searchbar.set_visible(False)

            # define a searchbar widget
            self.header.searchbar = Gtk.SearchBar.new()

            # we need to add this to the top of the source window
            # to-do this - find the first child and physically move this into
            # the second position in a box - the first position being the
            # searchbar
            children = source.get_children()
            print(children)
            # We assume the first container in a source is a GtkNotebook
            first = children[0]
            box = Gtk.Box()
            box.set_orientation(Gtk.Orientation.VERTICAL)
            box.pack_start(self.header.searchbar, False, True, 0)
            box.show_all()
            # so remove the notebook from the source
            Gtk.Container.remove(source, first)
            box.pack_start(first, True, True, 1)  # add the notebook to a box

            source.add(box)  # then add the box back to the source -
            # i.e. we added another parent

            self.header.register_moved_control(child=first,
                                               old_parent=source,
                                               new_parent=box)

            self.moveto_searchbar(toolbar, search, self.header.searchbar)
            entry.set_size_request(300, -1)

            self.header.searchbar.connect_entry(entry)
            # self.header.searchbar.show_all()
            self.header.searchbar.set_visible(False)

            search_button = Gtk.ToggleButton.new()
            sym = "preferences-system-search-symbolic"
            image = \
                Gtk.Image.new_from_icon_name(sym, Gtk.IconSize.SMALL_TOOLBAR)
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
            # self.header.searchbar.set_visible(True)

            self.remove_controls(self.header.end_box)
            search_button = self.end_controls[source]['search_button']
            self.header.current_search_button = search_button

            self.header.searchbar.show_all()
            self.header.searchbar.set_visible(search_button.get_active())

            self.header.end_box.add(search_button)
            self.header.end_box.reorder_child(search_button, 0)
            self.header.end_box.show_all()


class AltMusicLibraryController(AltGenericController):
    """
    music library controller
    """
    __gtype_name = 'AltMusicLibraryController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltMusicLibraryController, self).__init__(header)

    def valid_source(self, source):
        """
          override
        """

        return "LibrarySource" in type(source).__name__


class AltSoundCloudController(AltGenericController):
    """
    sound-cloud controller
    """
    __gtype_name = 'AltSoundCloudController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltSoundCloudController, self).__init__(header)

        self._has_toolbar = None

    def valid_source(self, source):
        """
          override
        """

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
        """
          override - here we want to actually remove the toolbar from the
          source so get the parent
        """

        parent_grid = toolbar.get_parent()
        parent_grid.remove(toolbar)
        searchbar.add(toolbar)

        self.header.register_moved_control(child=toolbar,
                                           old_parent=parent_grid,
                                           new_parent=searchbar)


class AltCoverArtBrowserController(AltGenericController):
    """
    CoverArtBrowser controller
    """
    __gtype_name = 'AltCoverArtBrowserController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltCoverArtBrowserController, self).__init__(header)

        self._has_toolbar = None

    def valid_source(self, source):
        """
          override
        """

        return "CoverArtBrowser" in type(source).__name__

    def get_category(self):
        return AltControllerCategory.LOCAL

    def get_toolbar(self, source):
        if not self._has_toolbar:
            search_box = self.find(source, 'toolbar', 'by_id')
            self._has_toolbar = search_box

        return self._has_toolbar

    def moveto_searchbar(self, toolbar, widget, searchbar):
        """
          override - here we want to actually remove the toolbar from the
          source so get the parent
        """

        parent_grid = toolbar.get_parent()
        parent_grid.remove(toolbar)
        searchbar.add(toolbar)
        searchbar.show_all()

        self.header.register_moved_control(child=toolbar,
                                           old_parent=parent_grid,
                                           new_parent=searchbar)

    def get_search_entry(self, toolbar):
        """
          override - use the GtkEntry in the coverartbrowser
        """

        entrysearch = self.find(toolbar, 'entry_search_alignment', 'by_id')
        entry = self.find(entrysearch, 'GtkEntry', 'by_name')

        return entrysearch, entry


class AltCoverArtPlaySourceController(AltGenericController):
    """
    CoverArtPlaySource controller
    """
    __gtype_name = 'AltCoverArtPlaySourceController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltCoverArtPlaySourceController, self).__init__(header)

        self._has_toolbar = None

    def valid_source(self, source):
        """
          override
        """

        return "CoverArtPlaySource" in type(source).__name__

    def get_category(self):
        return AltControllerCategory.LOCAL

    def get_toolbar(self, source):
        if not self._has_toolbar:
            self._has_toolbar = self.find(source, 'RBButtonBar', 'by_name')

        print("############", self._has_toolbar)
        return self._has_toolbar


class AltQueueController(AltGenericController):
    """
    RB QueueSource controller
    """
    __gtype_name = 'AltQueueController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltQueueController, self).__init__(header)

        self._gicon = Gio.ThemedIcon(name='audio-x-queue-symbolic')

    def valid_source(self, source):
        return "RBPlayQueueSource" in type(source).__name__

    def get_gicon(self, source):
        return self._gicon


class AltErrorsController(AltGenericController):
    """
    RB ErrorsSource controller
    """
    __gtype_name = 'AltErrorsController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltErrorsController, self).__init__(header)

        self._gicon = Gio.ThemedIcon(name='dialog-error-symbolic')

        self._source_types = ["RBImportErrorsSource",
                              "RBMissingFilesSource"]

    def valid_source(self, source):
        print(type(source).__name__)
        for source_type in self._source_types:
            if source_type in type(source).__name__:
                return True

    def get_category(self):
        return AltControllerCategory.LOCAL

    def get_gicon(self, source):
        return self._gicon


class AltRadioController(AltGenericController):
    """
    RB RadioSource controller
    """
    __gtype_name = 'AltRadioController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltRadioController, self).__init__(header)

        self._gicon = Gio.ThemedIcon(name='audio-radio-symbolic')

    def valid_source(self, source):
        return "RBIRadioSource" in type(source).__name__

    def get_gicon(self, source):
        return self._gicon

    def get_category(self):
        return AltControllerCategory.ONLINE

    def set_library_labels(self):
        self.header.set_library_labels(song_label=_('Stations'))

    def toolbar_visibility(self):
        return True  # radio source the source toolbar is always shown


class AltLastFMController(AltGenericController):
    """
    RB LastFMSource controller
    """
    __gtype_name = 'AltLastFMController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltLastFMController, self).__init__(header)

        self._libre_gicon = Gio.ThemedIcon(name='librefm-symbolic')
        self._lastfm_gicon = Gio.ThemedIcon(name='lastfm-symbolic')

    def valid_source(self, source):
        return "RBAudioscrobblerProfilePage" in type(source).__name__

    def get_gicon(self, source):
        # locale stuff
        cl = CoverLocale()
        cl.switch_locale(cl.Locale.RB)

        if source.props.name == _("Libre.fm"):
            return self._libre_gicon
        else:
            return self._lastfm_gicon

    def get_category(self):
        return AltControllerCategory.ONLINE


class AltPlaylistController(AltGenericController):
    """
    playlist controller
    """
    __gtype_name = 'AltPlaylistController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltPlaylistController, self).__init__(header)

        self._static_gicon = \
            Gio.ThemedIcon(name='audio-x-playlist-symbolic')
        self._auto_gicon = \
            Gio.ThemedIcon(name='audio-x-playlist-automatic-symbolic')

        self._toprated_gicon = Gio.ThemedIcon(name='starred-symbolic')
        self._recentlyadded_gicon = \
            Gio.ThemedIcon(name='audio-x-playlist-recently-added-symbolic')
        self._recentlyplayed_gicon = \
            Gio.ThemedIcon(name='audio-x-playlist-recently-played-symbolic')

    def valid_source(self, source):
        """
          override
        """
        return "PlaylistSource" in type(source).__name__

    def get_gicon(self, source):
        # locale stuff
        cl = CoverLocale()
        cl.switch_locale(cl.Locale.RB)
        print(source.props.name)
        if source.props.name == _('My Top Rated') \
                or source.props.name == 'My Top Rated':
            return self._toprated_gicon

        if source.props.name == _('Recently Added') \
                or source.props.name == 'Recently Added':
            return self._recentlyadded_gicon

        if source.props.name == _('Recently Played') \
                or source.props.name == 'Recently Played':
            return self._recentlyplayed_gicon

        if "StaticPlaylistSource" in type(source).__name__:
            return self._static_gicon
        else:
            return self._auto_gicon

    def get_category(self):
        return AltControllerCategory.PLAYLIST


class AltPodcastController(AltGenericController):
    """
    podcast controller
    """
    __gtype_name = 'AltPodcastController'

    def valid_source(self, source):
        """
          override
        """
        return 'RBPodcastMainSource' in type(source).__name__

    def get_category(self):
        return AltControllerCategory.LOCAL

    def set_library_labels(self):
        # locale stuff
        cl = CoverLocale()
        cl.switch_locale(cl.Locale.LOCALE_DOMAIN)

        self.header.set_library_labels(song_label=_('Podcasts'))

    def toolbar_visibility(self):
        return True  # podcast source the source toolbar is always shown


class AltStandardOnlineController(AltGenericController):
    """
      standard controller where we dont need specific customisation
    """
    __gtype_name = 'AltStandardOnlineController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltStandardOnlineController, self).__init__(header)

        self._source_types = ['MagnatuneSource',
                              'RBGriloSource',
                              'RadioBrowserSource']

    def valid_source(self, source):

        print(type(source).__name__)
        for source_type in self._source_types:
            if source_type in type(source).__name__:
                return True

        return False

    def get_category(self):
        return AltControllerCategory.ONLINE


class AltStandardLocalController(AltGenericController):
    """
      standard controller where we dont need specific customisation
    """
    __gtype_name = 'AltStandardLocalController'

    def __init__(self, header):
        """
        Initialises the object.
        """
        super(AltStandardLocalController, self).__init__(header)

        self._source_types = ['RBMtpSource']

    def valid_source(self, source):

        print(type(source).__name__)
        for source_type in self._source_types:
            if source_type in type(source).__name__:
                return True

        return False

    def get_category(self):
        return AltControllerCategory.LOCAL


class AltAndroidController(AltGenericController):
    '''
    android controller
    '''
    __gtype_name = 'AltAndroidController'

    def valid_source(self, source):
        '''
          override
        '''
        return 'RBAndroidSource' in type(source).__name__

    def get_category(self):
        return AltControllerCategory.LOCAL
