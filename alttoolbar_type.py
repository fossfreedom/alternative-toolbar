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

import os
import xml.etree.ElementTree as ET
from datetime import datetime, date
from xml.etree.ElementTree import SubElement

import rb
from alttoolbar_controller import AltAndroidController
from alttoolbar_controller import AltCoverArtBrowserController
from alttoolbar_controller import AltCoverArtPlaySourceController
from alttoolbar_controller import AltErrorsController
from alttoolbar_controller import AltGenericController
from alttoolbar_controller import AltLastFMController
from alttoolbar_controller import AltMusicLibraryController
from alttoolbar_controller import AltPlaylistController
from alttoolbar_controller import AltPodcastController
from alttoolbar_controller import AltQueueController
from alttoolbar_controller import AltRadioController
from alttoolbar_controller import AltSoundCloudController
from alttoolbar_controller import AltStandardLocalController
from alttoolbar_controller import AltStandardOnlineController
from alttoolbar_preferences import CoverLocale
from alttoolbar_preferences import GSetting
from alttoolbar_rb3compat import gtk_version
from alttoolbar_repeat import Repeat
from alttoolbar_sidebar import AltToolbarSidebar
from alttoolbar_widget import Slider
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import RB

class AT(object):
    @staticmethod
    def ToolbarRequestCallback(toolbar_type, box=None):
        """
        Callback method to obtain the type of toolbar together with the
        Gtk.Box where new UI elements can be added

        :param toolbar_type: AltToolbarBase derived object
        :param box: Gtk.Box or None if the toolbar does not have a UI where
        new objects can be added
        :return:
        """

        return toolbar_type, box


class AltToolbarBase(GObject.Object):
    """
    base for all toolbar types - never instantiated by itself
    """

    setup_completed = GObject.property(type=bool,
                                       default=False)
    # if changed to true then
    # setup_completed observers called back
    source_toolbar_visible = GObject.property(type=bool, default=True)

    def __init__(self):
        """
        Initialises the object.
        """
        super(AltToolbarBase, self).__init__()

        # remember details about when an entryview has been processed
        self._process_entryview = {}
        folder = RB.user_cache_dir() + "/alternate-toolbar"

        if not os.path.exists(folder):
            os.makedirs(folder)

        self._entryview_filename = folder + "/entryview_db.xml"

        self._save_cols_loop = 0

        db_version = "1"
        try:
            # if the db has not been deleted or is screwed up or is an older
            #  version than expected then
            # assume via the except we are starting from a clean db
            self._entryview_tree = ET.parse(self._entryview_filename)
            self._entryview_root = self._entryview_tree.getroot()

            db = self._entryview_root.find("database")
            if db.text != db_version:
                raise ValueError("wrong database version")

        except:
            text = """
                <root>
                   <pages>
                   </pages>
                </root>
                """

            self._entryview_root = ET.fromstring(text)
            db = SubElement(self._entryview_root, "database")
            db.text = db_version
            self._entryview_tree = ET.ElementTree(self._entryview_root)

        # bind the source-toolbar gsettings
        gs = GSetting()
        plugin_settings = gs.get_setting(gs.Path.PLUGIN)
        plugin_settings.bind(gs.PluginKey.SOURCE_TOOLBAR, self,
                             'source_toolbar_visible',
                             Gio.SettingsBindFlags.DEFAULT)

        self._async_functions = []  # array of functions to callback once the
        # toolbar has been setup
        self.connect('notify::setup-completed', self._on_setup_completed)

    def initialise(self, plugin):
        """
          one off initialisation call

          :param plugin is the plugin reference
        """

        self.plugin = plugin
        self.shell = plugin.shell

        self.find = plugin.find

        # finally - complete the headerbar setup after the database has fully
        # loaded because
        # rhythmbox has everything initiated at this point.

        self.startup_completed = False

        # self.shell.props.db.connect('load-complete', self.on_load_complete)

        # fire event anyway - scenario is when plugin is first activated post
        # rhythmbox having started
        def delayed(*args):
            if self.shell.props.selected_page:
                self.startup_completed = True
                self.on_startup()
                return False
            else:
                return True

        GLib.timeout_add(100, delayed)

    def get_custom_box(self):
        """

        :return: Gtk.Box
        """

        return None

    def post_initialise(self):
        """
          one off post initialisation call
        """
        tool_action = 'ToggleSourceMediaToolbar'
        action = self.plugin.toggle_action_group.get_action(tool_action)
        action.set_active(self.source_toolbar_visible)

    def on_startup(self, *args):
        """
          call after RB has completed its initialisation and selected the first
          view
        :param args:
        :return:
        """

        self.startup_completed = True
        self.reset_categories_pos(self.shell.props.selected_page)
        self.reset_toolbar(self.shell.props.selected_page)
        # lets hide the ghastly floating bar in RB 3.4.3
        cssdata = """
        .floating-bar {
            opacity: 0;
        }
        """
        cssprovider = Gtk.CssProvider.new()
        cssprovider.load_from_data(cssdata.encode())
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(
            self.shell.props.window.props.screen,
            cssprovider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER,
        )
        self.reset_entryview(self.shell.props.selected_page)

        if self.plugin.prefer_dark_theme:
            settings = Gtk.Settings.get_default()
            settings.set_property('gtk-application-prefer-dark-theme', True)

    def cleanup(self):
        """
          initiate a toolbar cleanup of resources and changes made to rhythmbox
        :return:
        """

        for page in self._process_entryview:
            self.disconnect(self._process_entryview[page]['size'])
            self.disconnect(self._process_entryview[page]['changed'])

        self.purge_builder_content()

    def on_search_toggle(self):
        """
           use the toolbar search
        """
        pass

    def set_visible(self, visible):
        """
           change the visibility of the toolbar
           :param bool
        """
        pass

    def show_cover(self, visible):
        """
           change the visibility of the toolbar coverart
           :param bool
        """
        pass

    def display_song(self, visible):
        """
           change the visibility of the song label on the toolbar
           :param bool
        """
        pass

    def play_control_change(self, player, playing):
        """
           control the display of various play-controls
           :param player is the shell-player
           :param playing bool as to whether a track is being played
        """
        pass

    def purge_builder_content(self):
        """
           one off cleanup routine called when the plugin in deactivated
        """
        pass

    def show_slider(self, visible):
        """
           show or hide the slider (progress bar)
           :param visible is a bool
        """
        pass

    def enable_slider(self, toggle):
        """
           enable or disable the slider (progress bar)
           :param toggle is a bool
        """
        pass

    def reset_categories_pos(self, page):
        """
           whenever a source changes this resets the source categories position
           reflect the changed source
           :param page - RBDisplayPage
        """
        print("reset categories position")
        if not page:
            print("no page")
            return

        if not hasattr(page.props, 'show_browser'):
            print("no browser")
            return

        if not self.plugin.horiz_categories:
            print("not horizontal")
            return

        propertyview = self.find(page, 'RBPropertyView', 'by_name')

        if propertyview is None:
            return

        parent = propertyview.get_parent()

        if isinstance(parent, Gtk.Paned):
            print("paned")
            parent.set_orientation(Gtk.Orientation.HORIZONTAL)
        else:
            print("not paned")
            pane = parent.get_parent()
            print(pane)
            parent.set_orientation(Gtk.Orientation.VERTICAL)
            pane.set_orientation(Gtk.Orientation.HORIZONTAL)

    def reset_entryview(self, page):
        """
           whenever a source changes this resets the source entryview to
           reflect the changed source
           :param page - RBDisplayPage
        """
        print("reset entryview")
        if not page:
            print("no page")
            return

        # workaround for GTK Crashing issues due to the user locale
        # non english locales (german for example) cause RB to
        # seg fault when moving columns - sadly need to disable
        # column moving capability for non-english locale users :(

        names = GLib.get_language_names()
        if ("en" not in names[0]):
            return

        try:
            entryview = page.get_entry_view()

            if not entryview:
                print("no entry view")
                return
        except:
            # some pages dont have the method to call!
            return

        try:
            treeview = entryview.get_child()
        except:
            treeview = self.find(entryview, 'GtkTreeView', 'by_name')
            # in RB v3.4.3 an RBEntryView doesnt have a child property...
            # plus the GtkTreeview is now hidden inside two further
            # containers - so we grab the tree view the hard-way of searching
            # for the Object Type

        def move_col(*args):
            cols = treeview.get_columns()

            # treeview.set_reorderable(True)

            current_cols = []
            base_col = None
            base_col_found = False

            for col in cols:
                title = col.props.title
                if title is not None and title.strip() != "":
                    if not base_col_found:
                        base_col = cols[cols.index(col) - 1]
                        base_col_found = True

                    print(title)
                    col.set_reorderable(True)
                    current_cols.append(col)

            if page in self._process_entryview:
                # disconnect previous signal handler if have been connected
                # before otherwise we'll trigger stuff when moving columns
                treeview.disconnect(self._process_entryview[page]['changed'])
                treeview.disconnect(self._process_entryview[page]['size'])

            # now move columns around depending upon saved values
            safe_name = self._safe_string(type(page).__name__)
            lookup = "pages/page[@name='" + safe_name + "']"
            element = self._entryview_root.find(lookup)

            if element is not None:
                # we've got something remembered to lets move cols around
                remembered_col_titles = element.text.split(',')
                remembered_cols = []

                for title in remembered_col_titles:
                    compare = title[1:-1]
                    for col in current_cols:
                        if col.props.title == compare:
                            remembered_cols.append(col)
                            break

                for i in range(len(remembered_cols)):
                    for col in current_cols:
                        if col.props.title == remembered_cols[i].props.title:
                            if current_cols.index(col) != i:
                                print(i, col.props.title)

                                if i == 0:
                                    treeview.move_column_after(col, base_col)
                                else:
                                    pos = i - 1

                                    treeview.move_column_after(col,
                                                               remembered_cols[
                                                                   pos])
                                break

                                # now reset column widths
                                # for col in current_cols:
                                #    safe_col_name = self._safe_string(
                                # col.props.title)

                                #    lookup = "pages/" + safe_name + "[
                                # @column='" + \
                                #             safe_col_name + "']"
                                #    col_node = self._entryview_root.find(
                                # lookup)

                                #    if col_node is not None:
                                #        col.set_fixed_width(int(
                                # col_node.get("width")))

            # now connect new signal handler
            ids = {}
            ids['changed'] = treeview.connect('columns-changed',
                                              self._entryview_column_changed,
                                              page)

            ids['size'] = treeview.connect('size-allocate',
                                           self._entryview_size_allocate, page)

            self._process_entryview[page] = ids

        # add a short delay otherwise RB will move after us nulling our
        # achievement
        Gdk.threads_add_timeout(GLib.PRIORITY_DEFAULT_IDLE, 10,
                                move_col)

    def _safe_string(self, s):
        return ''.join([i for i in s if i.isalpha()])

    def _entryview_size_allocate(self, treeview, allocation, page):
        self._entryview_column_changed(treeview, page)

    def _entryview_column_changed(self, treeview, page):
        # we basically don't want to process column-changed signals
        # when closing because these are fired by RB during the entry-view
        # cleanup & columns being deleted
        # so we work around this by looping for .5 secs before saving...
        # if we don't finish looping we assume that RB is closing and thus
        # dont really want to save ... yes a bit of a funny but its the best
        # we can do since RB doesnt have a close signal ... and just waiting
        # on the windows close event doesnt work because File-Quit cleans up
        # before actually closing.

        def _save_cols(*args):
            self._save_cols_loop += 1

            if self._save_cols_loop <= 6:
                return True

            self._save_cols_loop = 0
            self._save_entryview_cols(treeview, page)
            return False

        if self._save_cols_loop == 0:
            self._save_cols_loop = 1

            Gdk.threads_add_timeout(GLib.PRIORITY_DEFAULT_IDLE, 100,
                                    _save_cols)

        else:
            self._save_cols_loop = 1

    def _save_entryview_cols(self, treeview, page):
        print("entryview column changed")
        print(page)

        def quoted_string(array):
            return ','.join("'{0}'".format(x) for x in array)

        safe_name = self._safe_string(type(page).__name__)
        lookup = "pages/page[@name='" + safe_name + "']"
        node = self._entryview_root.find(lookup)

        pages = self._entryview_root.find("pages")

        if node is None:
            print("new node")
            node = SubElement(pages, 'page')
            node.set("name", safe_name)

        arr = []
        cols = treeview.get_columns()

        for col in cols:
            if col.props.title is not None and col.props.title != "":
                arr.append(col.props.title)
                # print (col.get_width())
                safe_col_name = self._safe_string(col.props.title)
                lookup = "pages/" + safe_name + "[@column='" + safe_col_name \
                         + "']"
                col_node = self._entryview_root.find(lookup)

                if col_node is None:
                    col_node = SubElement(pages, safe_name)
                    col_node.set("column", safe_col_name)

                col_node.set("width", str(col.get_width()))

        if len(arr) < 2:
            # nothing to do so quit before writing
            return

        output = quoted_string(arr)
        print(output)

        node.text = output

        self._indent_xml(self._entryview_root)
        self._entryview_tree.write(self._entryview_filename,
                                   xml_declaration=True)

    def _indent_xml(self, elem, level=0, more_sibs=False):
        i = "\n"
        if level:
            i += (level - 1) * '  '
        num_kids = len(elem)
        if num_kids:
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
                if level:
                    elem.text += '  '
            count = 0
            for kid in elem:
                self._indent_xml(kid, level + 1, count < num_kids - 1)
                count += 1
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
                if more_sibs:
                    elem.tail += '  '
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
                if more_sibs:
                    elem.tail += '  '

    def reset_toolbar(self, page):
        """
           whenever a source changes this resets the toolbar to reflect the
           changed source
           :param page - RBDisplayPage
        """
        print("reset toolbar")
        if not page:
            print("no page")
            return

        toolbar = self.find(page, 'RBSourceToolbar', 'by_name')

        if toolbar:
            print("found")
            toolbar.set_visible(self.source_toolbar_visible)
        else:
            print("not found")

        self.plugin.emit('toolbar-visibility', self.source_toolbar_visible)

    def setup_completed_async(self, async_function):
        """
          toolbars will callback once the setup has completed

        :param async_function: function callback
        :return:
        """

        if self.setup_completed:
            async_function(AT.ToolbarRequestCallback(self,
                                                     self.get_custom_box()))
        else:
            self._async_functions.append(async_function)

    def _on_setup_completed(self, *args):
        """
          one-off callback anybody who has registered to be notified when a
          toolbar has been completely setup
        :param args:
        :return:
        """
        if self.setup_completed:
            for callback_func in self._async_functions:
                callback_func(AT.ToolbarRequestCallback(self,
                                                        self.get_custom_box()))

    def source_toolbar_visibility(self, visibility):
        """
           called to toggle the source toolbar
        """
        print("source_bar_visibility")

        self.source_toolbar_visible = visibility
        # not self.source_toolbar_visible
        self.plugin.on_page_change(self.shell.props.display_page_tree,
                                   self.shell.props.selected_page)


class AltToolbarStandard(AltToolbarBase):
    """
    standard RB toolbar
    """
    __gtype_name = 'AltToolbarStandard'

    def __init__(self):
        """
        Initialises the object.
        """
        super(AltToolbarStandard, self).__init__()

    def post_initialise(self):
        self.volume_button = self.find(self.plugin.rb_toolbar,
                                       'GtkVolumeButton', 'by_id')
        self.volume_button.set_visible(self.plugin.volume_control)

        action = self.plugin.toggle_action_group.get_action('ToggleToolbar')
        action.set_active(not self.plugin.start_hidden)

        self.set_visible(not self.plugin.start_hidden)

        self.setup_completed = True

    def set_visible(self, visible):
        self.plugin.rb_toolbar.set_visible(visible)


class AltToolbarShared(AltToolbarBase):
    """
    shared components for the compact and headerbar toolbar types
    """

    def __init__(self):
        """
        Initialises the object.
        """
        super(AltToolbarShared, self).__init__()

        # Prepare Album Art Displaying
        self.album_art_db = GObject.new(RB.ExtDB, name="album-art")

        what, width, height = Gtk.icon_size_lookup(Gtk.IconSize.SMALL_TOOLBAR)
        self.icon_width = width
        self.cover_pixbuf = None
        self._controllers = {}
        self._tooltip_exceptions = ['album_cover']
        self._moved_controls = []

    def initialise(self, plugin):
        super(AltToolbarShared, self).initialise(plugin)

        ui = rb.find_plugin_file(plugin, 'ui/alttoolbar.ui')

        cl = CoverLocale()
        builder = Gtk.Builder()
        builder.set_translation_domain(cl.Locale.LOCALE_DOMAIN)
        builder.add_from_file(ui)

        self.load_builder_content(builder)
        self.connect_builder_content(builder)

        self._controllers['generic'] = AltGenericController(self)
        # every potential source should have its own controller - we use this
        # to categorise the source and provide specific capability for
        # inherited classes where a controller is not specified then a generic
        # controller is used i.e. use add_controller method to add a controller
        self.add_controller(AltMusicLibraryController(self))
        self.add_controller(AltSoundCloudController(self))
        self.add_controller(AltCoverArtBrowserController(self))
        self.add_controller(AltCoverArtPlaySourceController(self))
        self.add_controller(AltQueueController(self))
        self.add_controller(AltStandardOnlineController(self))
        self.add_controller(AltStandardLocalController(self))
        self.add_controller(AltRadioController(self))
        self.add_controller(AltLastFMController(self))
        self.add_controller(AltPlaylistController(self))
        self.add_controller(AltErrorsController(self))
        self.add_controller(AltPodcastController(self))
        self.add_controller(AltAndroidController(self))

        # support RTL
        for control, icon_name in \
                [(self.prev_button, 'media-skip-backward-symbolic'),
                 (self.play_button, 'media-playback-start-symbolic'),
                 (self.next_button, 'media-skip-forward-symbolic')]:
            image = control.get_child()
            icon_name = self.request_rtl_icon(control, icon_name)
            image.set_from_icon_name(icon_name, image.props.icon_size)

        # now move current RBDisplayPageTree to listview stack
        display_tree = self.shell.props.display_page_tree
        self.display_tree_parent = display_tree.get_parent()
        self.display_tree_parent.remove(display_tree)
        self.stack = Gtk.Stack()
        tran_type = Gtk.StackTransitionType.SLIDE_LEFT_RIGHT
        self.stack.set_transition_type(tran_type)
        self.stack.set_transition_duration(1000)

        image_name = 'view-list-symbolic'

        box_listview = Gtk.Box()
        box_listview.pack_start(display_tree, True, True, 0)
        # box_listview.show_all()
        self.stack.add_named(box_listview, "listview")
        self.stack.child_set_property(box_listview, "icon-name", image_name)
        self.stack.show_all()

        self.display_tree_parent.pack1(self.stack, True, True)

        # if 1==2: #self.plugin.enhanced_sidebar:
        toolbar = self.find(display_tree, 'GtkToolbar', 'by_name')
        # context = toolbar.get_style_context()
        # context.add_class('toolbar')
        box = self.find(toolbar, 'GtkBox', 'by_name')
        # box.props.margin_top = 2
        # box.props.margin_bottom = 0
        # box.props.margin_left = 5
        context = box.get_style_context()
        context.add_class('linked')
        # parent = box.get_parent()
        # parent.remove(box)
        # parent_toolbar = toolbar.get_parent()
        # parent_toolbar.remove(toolbar)
        # display_tree.attach(box, 0, 10, 1 ,1 )

        # child, new-parent, old-parent
        # self._moved_controls.append((box, display_tree, parent))
        # self._moved_controls.append((toolbar, None, parent_toolbar))

        # find the actual GtkTreeView in the RBDisplayTree and remove it
        self.rbtree = self.find(display_tree, 'GtkTreeView', 'by_name')
        self.rbtreeparent = self.rbtree.get_parent()
        self.rbtreeparent.remove(self.rbtree)

        self.sidebar = None

    def post_initialise(self):
        super(AltToolbarShared, self).post_initialise()
        cl = CoverLocale()
        cl.switch_locale(cl.Locale.LOCALE_DOMAIN)
        self.volume_button.props.value = \
            self.shell.props.shell_player.props.volume
        self.volume_button.bind_property("value",
                                         self.shell.props.shell_player,
                                         "volume",
                                         Gio.SettingsBindFlags.DEFAULT)

        self.volume_button.set_visible(self.plugin.volume_control)
        self.volume_button.set_relief(Gtk.ReliefStyle.NORMAL)
        child = self.volume_button.get_child()
        child.set_margin_left(5)
        child.set_margin_right(5)

        if self.plugin.inline_label:
            self.song_box.remove(self.song_button_label)

        self.song_progress = Slider(self.shell.props.shell_player)
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
                # https://gitlab.gnome.org/GNOME/gtk/issues/939
                # the above issue is why you see actionhelper mismatch
                # errors
                a.set_action_target_value(GLib.Variant("b", True))
                if not a.get_sensitive():
                    a.set_detailed_action_name("app." + b)


        # The Play-Repeat button is subject to the plugins Repeat All/one song
        # capability
        self._repeat = Repeat(self.shell, self.repeat_toggle)

        if gtk_version() >= 3.12:
            self.cover_popover = Gtk.Popover.new(self.album_cover)
            image = Gtk.Image.new()
            self.cover_popover.add(image)

            self._popover_inprogress = 0
            self.cover_popover.set_modal(False)
            self.cover_popover.connect('leave-notify-event',
                                       self._on_cover_popover_mouse_over)
            self.cover_popover.connect('enter-notify-event',
                                       self._on_cover_popover_mouse_over)
            # detect when mouse moves out of the cover image
            # (it has a parent eventbox)
            box = self.album_cover_eventbox
            box.connect('leave-notify-event',
                        self._on_cover_popover_mouse_over)
            box.connect('enter-notify-event',
                        self._on_cover_popover_mouse_over)

        cl.switch_locale(cl.Locale.RB)

    def on_startup(self, *args):
        super(AltToolbarShared, self).on_startup(*args)

        if self.plugin.enhanced_sidebar:
            self.sidebar = AltToolbarSidebar(self, self.rbtree)
            self.sidebar.show_all()
            self.rbtreeparent.add(self.sidebar)
        else:
            self.rbtreeparent.add(self.rbtree)

            # self.shell.add_widget(self.rbtree, RB.ShellUILocation.SIDEBAR,
            # expand=True, fill=True)

    def register_moved_control(self, child, old_parent, new_parent=None):
        """
           convenience function to save the GTK child & parents when they are
           moved.
           we use this info to cleanup when quitting RB - we need to move
           stuff back because
           otherwise there are random crashes due to memory deallocation issues

        :param child: GTK Widget
        :param old_parent: original GTK container that the child was moved from
        :param new_parent: new GTK container that the child was added to (may
        just have removed without moving)
        :return:
        """

        # store as a tuple: child, new-parent, old-parent
        self._moved_controls.append((child, new_parent, old_parent))

    def cleanup(self):
        """
          extend
        :return:
        """

        super(AltToolbarShared, self).cleanup()

        if self.sidebar:
            self.sidebar.cleanup()

        self.display_tree_parent.remove(self.stack)
        self.display_tree_parent.pack1(self.shell.props.display_page_tree)
        if self.sidebar:
            self.rbtreeparent.remove(self.sidebar)  # remove our sidebar
            self.rbtreeparent.add(self.rbtree)  # add the original GtkTree view

        print("####")
        # child, new-parent, old-parent
        for child, new_parent, old_parent in reversed(self._moved_controls):
            if new_parent:
                new_parent.remove(child)
            print(child)
            print(new_parent)
            print(old_parent)
            if isinstance(old_parent, Gtk.Grid):
                print("attaching to grid")
                old_parent.attach(child, 0, 0, 1, 1)
            else:
                print("adding to parent")
                old_parent.add(child)

    def add_controller(self, controller):
        """
          register a new controller
        """
        if controller not in self._controllers:
            self._controllers[controller] = controller

    def is_controlled(self, source):
        """
          determine if the source has a controller
          return bool, controller
             if no specific controller (False) then the generic controller
             returned
        """

        if source in self._controllers:
            return True, self._controllers[source]

        # loop through controllers to find one that is most applicable
        for controller_type in self._controllers:
            if self._controllers[controller_type].valid_source(source):
                return True, self._controllers[controller_type]

        return False, self._controllers['generic']

    def show_cover_tooltip(self, tooltip):
        if (self.cover_pixbuf is not None):
            scale = self.cover_pixbuf.scale_simple(300, 300,
                                                   GdkPixbuf.InterpType.HYPER)
            if gtk_version() >= 3.12:
                if self.cover_popover.get_visible():
                    return False
                image = self.cover_popover.get_child()
                image.set_from_pixbuf(scale)
                self.cover_popover.show_all()
            else:
                tooltip.set_icon(scale)
            return True
        else:
            return False

    def _on_cover_popover_mouse_over(self, widget, eventcrossing):
        if eventcrossing.type == Gdk.EventType.ENTER_NOTIFY:
            if self._popover_inprogress == 0:
                self._popover_inprogress = 1
            else:
                self._popover_inprogress = 2

            self._popover_inprogress_count = 0
            print("enter")
        else:
            print("exit")
            self._popover_inprogress = 3

        # print (eventcrossing.type)

        def delayed(*args):
            if self._popover_inprogress == 3:
                self._popover_inprogress_count += 1
                if self._popover_inprogress_count < 5:
                    return True

                self.cover_popover.hide()
                self._popover_inprogress = 0
                return False
            else:
                return True

        if self._popover_inprogress == 1:
            print("addding timeout")
            self._popover_inprogress = 2
            GLib.timeout_add(100, delayed)

    def show_slider(self, visibility):
        self.song_box.set_visible(visibility)

    def enable_slider(self, toggle):
        self.song_progress.set_sensitive(toggle)

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

        if (entry is None):
            # self.song_button_label.set_text("")
            self.inline_box.set_visible(False)
            return False

        self.inline_box.set_visible(True)

        db = self.shell.props.db
        stream_title = \
            db.entry_request_extra_metadata(entry,
                                            RB.RHYTHMDB_PROP_STREAM_SONG_TITLE)
        stream_artist = \
            db.entry_request_extra_metadata(entry,
                                            RB.RHYTHMDB_PROP_STREAM_SONG_ARTIST)

        def set_labels(title, artist):
            for child in self.inline_box:
                self.inline_box.remove(child)

            self.song_title = Gtk.Label()
            self.song_title.set_markup(title)
            self.song_title.set_ellipsize(Pango.EllipsizeMode.END)
            self.song_title.show()
            self.inline_box.pack_start(self.song_title, False, True, 0)
            print(artist)
            if artist != "" or artist:
                print("adding artist")
                self.song_artist = Gtk.Label()
                self.song_artist.set_markup(artist)
                self.song_artist.set_ellipsize(Pango.EllipsizeMode.END)
                self.song_artist.show()
                self.inline_box.pack_start(self.song_artist, False, True, 1)

        if stream_title:
            print("stream_title")
            if stream_artist:
                artist_markup = "<small>{artist}</small>".format(
                    artist=GLib.markup_escape_text(stream_artist))
            else:
                artist_markup = ""

            title_markup = "<b>{title}</b>".format(
                title=GLib.markup_escape_text(stream_title))

            set_labels(title_markup, artist_markup)

            return True

        album = entry.get_string(RB.RhythmDBPropType.ALBUM)
        if not album or album == "":
            print("album")
            title_markup = "<b>{title}</b>".format(
                title=GLib.markup_escape_text(
                    entry.get_string(RB.RhythmDBPropType.TITLE)))

            artist = entry.get_string(RB.RhythmDBPropType.ARTIST)
            if artist and artist != "":
                artist_markup = "<small>{artist}</small>".format(
                    artist=GLib.markup_escape_text(
                        entry.get_string(RB.RhythmDBPropType.ARTIST)))
            else:
                artist_markup = ""

            set_labels(title_markup, artist_markup)

            return True

        if self.plugin.playing_label:
            print("playing_label")
            year = entry.get_ulong(RB.RhythmDBPropType.DATE)
            if year == 0:
                year = date.today().year
            else:
                year = datetime.fromordinal(year).year

            title_markup = "<b>{album}</b>".format(
                album=GLib.markup_escape_text(
                    entry.get_string(RB.RhythmDBPropType.ALBUM)))
            artist_markup = "<small>{genre} - {year}</small>".format(
                genre=GLib.markup_escape_text(
                    entry.get_string(RB.RhythmDBPropType.GENRE)),
                year=GLib.markup_escape_text(str(year)))

            set_labels(title_markup, artist_markup)
        else:
            print("not playing_label")
            title_markup = "<b>{title}</b>".format(
                title=GLib.markup_escape_text(
                    entry.get_string(RB.RhythmDBPropType.TITLE)))

            artist_markup = "<small>{artist}</small>".format(
                artist=GLib.markup_escape_text(
                    entry.get_string(RB.RhythmDBPropType.ARTIST)))

            set_labels(title_markup, artist_markup)

        return True

    def _combined_progress_label(self, entry):
        """
           utility function to calculate the label to be used when a progress
           bar has the label above it
           :param RBEntry
        """

        if (entry is None):
            self.song_button_label.set_label("")
            return False

        db = self.shell.props.db
        stream_title = \
            db.entry_request_extra_metadata(entry,
                                            RB.RHYTHMDB_PROP_STREAM_SONG_TITLE)
        stream_artist = \
            db.entry_request_extra_metadata(entry,
                                            RB.RHYTHMDB_PROP_STREAM_SONG_ARTIST)

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
            self.song_button_label.set_markup(
                "<small><b>{title}</b></small>".format(
                    title=GLib.markup_escape_text(
                        entry.get_string(RB.RhythmDBPropType.TITLE))))
            return True

        if self.plugin.playing_label:
            year = entry.get_ulong(RB.RhythmDBPropType.DATE)
            if year == 0:
                year = date.today().year
            else:
                year = datetime.fromordinal(year).year

            self.song_button_label.set_markup(
                "<small>{album} - {genre} - {year}</small>".format(
                    album=GLib.markup_escape_text(
                        entry.get_string(RB.RhythmDBPropType.ALBUM)),
                    genre=GLib.markup_escape_text(
                        entry.get_string(RB.RhythmDBPropType.GENRE)),
                    year=GLib.markup_escape_text(str(year))))
        else:
            self.song_button_label.set_markup(
                "<small><b>{title}</b> {album} - {artist}</small>".format(
                    title=GLib.markup_escape_text(
                        entry.get_string(RB.RhythmDBPropType.TITLE)),
                    album=GLib.markup_escape_text(
                        entry.get_string(RB.RhythmDBPropType.ALBUM)),
                    artist=GLib.markup_escape_text(
                        entry.get_string(RB.RhythmDBPropType.ARTIST))))

        return True

    def display_song_album_art_callback(self, *args):
        # key, filename, data, entry):
        """
          RBExtDB signal callback to display the album-art
        """
        # rhythmbox 3.2 breaks the API - need to find the parameter with the
        # pixbuf
        data = None
        for data in args:
            if isinstance(data, GdkPixbuf.Pixbuf):
                break

        if ((data is not None) and (isinstance(data, GdkPixbuf.Pixbuf))):
            self.cover_pixbuf = data
            scale_cover = \
                self.cover_pixbuf.scale_simple(34, 34,
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

    def request_rtl_icon(self, control, icon_name):
        rtl_name = {}
        rtl_name["media-playback-start-symbolic"] = \
            "media-playback-start-rtl-symbolic"
        rtl_name["media-skip-forward-symbolic"] = \
            "media-skip-forward-rtl-symbolic"
        rtl_name["media-skip-backward-symbolic"] = \
            "media-skip-backward-rtl-symbolic"

        name = icon_name
        if gtk_version() < 3.12:
            if control.get_direction() == Gtk.TextDirection.RTL:
                name = rtl_name[icon_name]

        return name

    def play_control_change(self, player, playing):
        image = self.play_button.get_child()
        if (playing):
            if player.get_active_source().can_pause():
                icon_name = "media-playback-pause-symbolic"
            else:
                icon_name = "media-playback-stop-symbolic"

        else:
            icon_name = self.request_rtl_icon(self.play_button,
                                              "media-playback-start-symbolic")

        image.set_from_icon_name(icon_name, image.props.icon_size)

    # Builder related utility functions... ####################################

    def load_builder_content(self, builder):
        if (not hasattr(self, "__builder_obj_names")):
            self.__builder_obj_names = list()

        for obj in builder.get_objects():
            if (isinstance(obj, Gtk.Buildable)):
                name = Gtk.Buildable.get_name(obj).replace(' ', '_')
                self.__dict__[name] = obj
                self.__builder_obj_names.append(name)

                if not self.plugin.show_tooltips and obj.get_has_tooltip():
                    if name not in self._tooltip_exceptions:
                        obj.set_has_tooltip(False)

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

        if (hasattr(target, h_name_internal)):
            handler = getattr(target, h_name_internal)
        else:
            handler = eval(handler_name)

        object.connect(sig_name, handler)

    def purge_builder_content(self):
        for name in self.__builder_obj_names:
            o = self.__dict__[name]
            if (isinstance(o, Gtk.Widget)):
                o.destroy()
            del self.__dict__[name]

        del self.__builder_obj_names

    # Signal Handlers
    def _sh_bigger_cover(self, cover, x, y, key, tooltip):
        return self.show_cover_tooltip(tooltip)


class AltToolbarCompact(AltToolbarShared):
    """
    compact RB toolbar
    """
    __gtype_name = 'AltToolbarCompact'

    def __init__(self):
        """
        Initialises the object.
        """
        super(AltToolbarCompact, self).__init__()

    def initialise(self, plugin):
        super(AltToolbarCompact, self).initialise(plugin)

        self._setup_compactbar()

        if self.shell.props.application.get_menubar() == None:
            builder = Gtk.Builder()
            ui = rb.find_plugin_file(self.plugin, 'ui/altmenubar.ui')
            cl = CoverLocale()
            builder.set_translation_domain(cl.Locale.RB)
            builder.add_from_file(ui)
            menubar = builder.get_object("menubar")
            self.shell.props.application.link_shared_menus(menubar)
            self.shell.props.application.set_menubar(menubar)

            self.load_builder_content(builder)

    def on_startup(self, *args):
        super(AltToolbarCompact, self).on_startup(*args)

        self.setup_completed = True

    def _setup_compactbar(self):

        # self.window_control_item.add(self._window_controls())

        action = self.plugin.toggle_action_group.get_action('ToggleToolbar')

        self.small_bar.get_style_context().add_class(
            Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)

        # add settings menu depending if there is no applications menu
        # available
        # appshell = ApplicationShell(self.shell)
        menu = self.shell.props.application.get_menubar()

        if not menu or self.plugin.app_menu:
            menu_button = Gtk.MenuButton.new()
            if gtk_version() >= 3.14:
                symbol = "open-menu-symbolic"
                menu_button.set_margin_start(3)
            else:
                symbol = "emblem-system-symbolic"
                menu_button.set_margin_left(3)

            image = Gtk.Image.new_from_icon_name(symbol,
                                                 Gtk.IconSize.SMALL_TOOLBAR)
            menu_button.add(image)
            menu = self.shell.props.application.get_shared_menu('app-menu')
            menu_button.set_menu_model(menu)
            self.end_box.add(menu_button)

        if not self.plugin.start_hidden:
            self.shell.add_widget(self.small_bar,
                                  RB.ShellUILocation.MAIN_TOP, expand=False,
                                  fill=False)
            self.show_small_bar()
            action.set_active(True)
            print("not hidden but compact")
        else:
            action.set_active(False)

        self.plugin.rb_toolbar.hide()

    def get_custom_box(self):
        return self.end_box

    def set_visible(self, visible):
        if visible:
            print("show_compact")
            self.shell.add_widget(self.small_bar,
                                  RB.ShellUILocation.MAIN_TOP, expand=False,
                                  fill=False)
            self.show_small_bar()
            self.volume_button.set_visible(self.plugin.volume_control)
        else:
            print("hide compact")
            self.shell.remove_widget(self.small_bar,
                                     RB.ShellUILocation.MAIN_TOP)


class AltToolbarHeaderBar(AltToolbarShared):
    """
    headerbar RB toolbar
    """
    __gtype_name = 'AltToolbarHeaderBar'

    __gsignals__ = {
        'song-category-clicked': (GObject.SIGNAL_RUN_LAST, None, (bool,))
    }

    # song-category-clicked signal emitted when song-categoy buttons clicked -
    # param True if Song clicked

    def __init__(self):
        """
        Initialises the object.
        """
        super(AltToolbarHeaderBar, self).__init__()

        self.sources = {}
        self.searchbar = None

        self.source_toolbar_visible = False  # override - for headerbars source
        # toolbar is not visible

        self._always_visible_sources = {}

    def _on_key_press(self, widget, event):
        self.searchbar.handle_event(event)
        keyname = Gdk.keyval_name(event.keyval)
        #if keyname == 'Escape' and self.current_search_button:
            #self.current_search_button.set_active(False)
            #self.searchbar.set_search_mode(False)
            #self.search_button_toggled(self.current_search_button)

        if event.state and Gdk.ModifierType.CONTROL_MASK:
            if keyname == 'f' and self.current_search_button:
                self.current_search_button.set_active(
                    not self.current_search_button.get_active())

    def on_search_toggle(self):
        if self.current_search_button.get_active() and \
           not self.searchbar.get_search_mode():
           self.searchbar.set_search_mode(True)
           return

        self.current_search_button.set_active(
            not self.current_search_button.get_active())

        self.searchbar.set_search_mode(self.current_search_button.get_active())

    def initialise(self, plugin):
        super(AltToolbarHeaderBar, self).initialise(plugin)

        self.main_window = self.shell.props.window

        self._setup_playbar()
        self._setup_headerbar()

        # hook the key-press for the application window
        #self.shell.props.window.connect("key-press-event", self._on_key_press)

    def add_always_visible_source(self, source):
        """
           remember which sources always have the song-category buttons enabled
        """
        self._always_visible_sources[source] = source

    def on_startup(self, *args):
        super(AltToolbarHeaderBar, self).on_startup(*args)

        if self.shell.props.selected_page.props.show_browser:
            self.library_browser_radiobutton.set_active(True)

        self.library_radiobutton_toggled(None)

        self.library_browser_radiobutton.connect('toggled',
                                                 self.library_radiobutton_toggled)
        self.library_song_radiobutton.connect('toggled',
                                              self.library_radiobutton_toggled)

        self._set_toolbar_controller()

        self.setup_completed = True

    def _setup_playbar(self):
        """
          setup the play controls at the bottom part of the application
        """

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
        action = self.plugin.appshell.lookup_action('', 'statusbar-visible',
                                                    'win')
        if action:
            action.set_active(True)

    def search_button_toggled(self, search_button):
        def delay_hide(*args):
            # we use a delay to allow the searchbar minimise effect to be
            # visible
            self.searchbar.set_visible(False)
            self.searchbar.set_search_mode(False)
            search_button.set_active(False)

        if search_button.get_active():
            self.searchbar.set_visible(True)
            self.searchbar.set_search_mode(True)
        else:
            GLib.timeout_add(350, delay_hide)

    def set_library_labels(self, song_label=None, category_label=None):
        # locale stuff
        cl = CoverLocale()
        cl.switch_locale(cl.Locale.LOCALE_DOMAIN)
        if not song_label:
            self.library_song_radiobutton.set_label(_('Songs'))
        else:
            self.library_song_radiobutton.set_label(
                cl.get_translation(song_label))

        if not category_label:
            self.library_browser_radiobutton.set_label(_('Categories'))
        else:
            self.library_browser_radiobutton.set_label(
                cl.get_translation(category_label))

        cl.switch_locale(cl.Locale.RB)

    def library_radiobutton_toggled(self, toggle_button):
        print("library_radiobutton_toggled")
        if not self.setup_completed:
            return

        controlled, current_controller = self.is_controlled(
            self.shell.props.selected_page)
        current_controller.set_library_labels()

        if toggle_button:
            self.emit('song-category-clicked',
                      self.library_song_radiobutton.get_active())

        self._resize_source(self.shell.props.selected_page)

        val, button = self.is_browser_view(self.shell.props.selected_page)
        if not val:
            return

        val = True
        if self.library_song_radiobutton.get_active():
            print("song active")
            val = False

        self.shell.props.selected_page.props.show_browser = val

    def has_button_with_label(self, source, label):
        """
           returns bool, button where the button has a given label
        """
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
        """
           returns bool, browser-button where this is a browser-view
           i.e. assume if there is a browser button this makes it a
           browser-view
        """

        return self.has_button_with_label(source, _("Browse"))

    def get_custom_box(self):
        return self.start_box

    def _setup_headerbar(self):

        cl = CoverLocale()
        # define the main buttons for the headerbar
        builder = Gtk.Builder()
        ui = rb.find_plugin_file(self.plugin, 'ui/altlibrary.ui')
        builder.set_translation_domain(cl.Locale.LOCALE_DOMAIN)
        builder.add_from_file(ui)

        self.load_builder_content(builder)

        view_name = _("Categories")
        self.library_browser_radiobutton.set_label(view_name)

        self.headerbar = Gtk.HeaderBar.new()
        self.headerbar.set_show_close_button(True)

        self.main_window.set_titlebar(self.headerbar)
        # this is needed for gnome-shell to replace the decoration
        self.main_window.set_show_menubar(False)
        self.plugin.rb_toolbar.hide()

        self.start_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        # left side box
        self.headerbar.pack_start(self.start_box)

        self.headerbar.set_custom_title(self.library_box)

        self._end_box_controls = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        # right side box
        self.end_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        # any source defined controls
        self._end_box_controls.add(self.end_box)

        # add a source toggle button
        source_button = Gtk.ToggleButton.new()
        source_button.set_action_name("app.ToggleSourceMediaToolbar")

        symbol = "view-more-horizontal-symbolic"
        if gtk_version() >= 3.14:
            source_button.set_margin_start(6)
        else:
            source_button.set_margin_left(6)

        image = Gtk.Image.new_from_icon_name(symbol,
                                             Gtk.IconSize.SMALL_TOOLBAR)
        source_button.add(image)
        self._end_box_controls.add(source_button)

        # GNOME design upstream is that main appmenu options should be
        # within reach of the headerbar with the traditional
        # appmenu reduced to the occasionally used options
        # We will reduce the appmenu to just Help, About and Quit option

        menu_button = Gtk.MenuButton.new()
        if gtk_version() >= 3.14:
            symbol = "open-menu-symbolic"
            menu_button.set_margin_start(6)
        else:
            symbol = "emblem-system-symbolic"
            menu_button.set_margin_left(6)

        image = Gtk.Image.new_from_icon_name(symbol,
                                             Gtk.IconSize.SMALL_TOOLBAR)
        menu_button.add(image)
        menu = self.shell.props.application.get_shared_menu('app-menu')
        menu_button.set_menu_model(menu)
        self._end_box_controls.add(menu_button)
        #menu.remove(3)  # help about quit

        #cl.switch_locale(cl.Locale.RB)
        #appmenu = Gio.Menu.new()
        #appmenu.append(_("_Help"), "app.help")
        #appmenu.append(_("_About"), "app.about")
        #appmenu.append(_("_Quit"), "app.quit")
        #app = self.shell.props.application
        #app.set_app_menu(appmenu)

        self.headerbar.pack_end(self._end_box_controls)
        self.headerbar.show_all()

        controlled, current_controller = \
            self.is_controlled(self.shell.props.selected_page)
        current_controller.set_library_labels()

        action = self.plugin.toggle_action_group.get_action('ToggleToolbar')
        if not self.plugin.start_hidden:
            action.set_active(True)
            print("not hidden")
        else:
            action.set_active(False)
            self.set_visible(False)

    def _resize_source(self, page):
        if page:
            child = self.find(page, 'GtkGrid', "by_name")
            # hard-coded test for sources where grid is this value
            if child and child.props.margin_top == 6:
                child.props.margin_top = 0

    def reset_toolbar(self, page):
        print(page)
        super(AltToolbarHeaderBar, self).reset_toolbar(page)

        self.library_radiobutton_toggled(None)
        self._set_toolbar_controller()

        self._resize_source(page)

        ret, controller = self.is_controlled(page)
        controller.set_library_labels()
        if controller.toolbar_visibility() is not None:
            toolbar = controller.get_toolbar(page)
            toolbar.set_visible(controller.toolbar_visibility())

    def _set_toolbar_controller(self):

        ret_generic_bool, generic_controller = self.is_controlled('generic')
        if not ret_generic_bool:
            return

        if self.shell.props.selected_page not in self.sources:
            ret_bool, controller = \
                self.is_controlled(self.shell.props.selected_page)
            self.sources[self.shell.props.selected_page] = controller

        current_controller = self.sources[self.shell.props.selected_page]
        current_controller.update_controls(self.shell.props.selected_page)

    def set_visible(self, visible):
        self.small_bar.set_visible(visible)

    def set_library_box_sensitive(self, sensitivity):
        sensitive = sensitivity

        if self.shell.props.selected_page in self._always_visible_sources:
            sensitive = True

        self.library_box.set_sensitive(sensitive)
