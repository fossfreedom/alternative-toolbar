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

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Pango
from gi.repository import RB
from gi.repository import Gio

from alttoolbar_controller import AltControllerCategory
from alttoolbar_preferences import GSetting

class AltToolbarSidebar(Gtk.TreeView):

    expanders = GObject.property(type=str, default='{1:True}')

    def __init__(self, toolbar, rbtree):
        '''
        Initialises the object.
        '''
        super(AltToolbarSidebar, self).__init__()

        self.shell = toolbar.shell
        self.toolbar = toolbar
        self.plugin = toolbar.plugin
        self.rbtree = rbtree

        self.set_name("AltToolbarSideBar")
        self._category = {}
        self._last_click_source = None
        
        self._user_clicked = False

        gs = GSetting()
        plugin_settings = gs.get_setting(gs.Path.PLUGIN)
        plugin_settings.bind(gs.PluginKey.EXPANDERS, self, 'expanders',
                                  Gio.SettingsBindFlags.DEFAULT)

        # title, source, visible
        self.treestore = Gtk.TreeStore.new([str, GObject.Object, bool])
        self.treestore_filter = self.treestore.filter_new(root=None)
        self.treestore_filter.set_visible_column(2)

        self.set_model(self.treestore_filter)
        context = self.get_style_context()
        context.add_class(Gtk.STYLE_CLASS_SIDEBAR)
        self.set_headers_visible(False)

        # define the headers - not visible by default
        def define_category(text, category):
            local = self.treestore.append(None)
            self.treestore[local] = [text, None, False]
            self._category[category] = local

        define_category(_("Local collection"), AltControllerCategory.LOCAL)
        define_category(_("Online sources"), AltControllerCategory.ONLINE)
        define_category(_("Other sources"), AltControllerCategory.OTHER)
        define_category(_("Playlists"), AltControllerCategory.PLAYLIST)

        def delayed(*args):
            model = self.shell.props.display_page_model
            rootiter = model.get_iter_first()
            depth = 0
            self._traverse_rows(model, rootiter, None, depth)

            # switch on/off headers depending upon what's in the model
            self._refresh_headers()

            # tidy up syncing by connecting signals
            self._connect_signals()

            # now expand or collapse each expander that we have saved from a previous session
            expanders=eval(self.expanders)

            print (expanders)
            print (self.expanders)
            for category in expanders:
                print (category)
                path = self.treestore.get_path(self._category[category])

                if path and expanders[category]:
                    #self._user_clicked = True
                    self.expand_row(path, False) #expanders[category])

            return False

        GLib.timeout_add_seconds(1, delayed)

        column = Gtk.TreeViewColumn.new()

        pixbuf_renderer = Gtk.CellRendererPixbuf()
        column.pack_start(pixbuf_renderer, False)
        renderer = Gtk.CellRendererText()
        renderer.connect('edited', self.on_renderertext_edited)
        self.text_renderer = renderer
        column.pack_start(renderer, False)

        column.set_cell_data_func(pixbuf_renderer, self._set_pixbuf)
        column.set_cell_data_func(renderer, self._set_text)

        self.tree_column = column

        self.append_column(column)
        self.show_all()
        self.set_can_focus(True)

    def _connect_signals(self):
        # display_page_model signals to keep the sidebar model in sync
        model = self.shell.props.display_page_model
        #model.props.child_model.connect('row-inserted', self._model_page_inserted)
        #model.connect('row-inserted', self._model_page_inserted)
        self._cpi = model.connect('page-inserted', self._model_page_inserted)
        self._crd = model.connect('row-deleted', self._model_page_deleted)
        self._crc = model.connect('row-changed', self._model_page_changed)

        # when we click on the sidebar - need to keep the display_page_tree in sync
        self.connect('button-press-event', self._row_click)
        # and visa versa
        self.shell.props.display_page_tree.connect('selected', self._display_page_tree_selected)
        self.shell.props.shell_player.connect('playing-song-changed', self._on_playing_song_changed)

    def cleanup(self):
        model = self.shell.props.display_page_model
        model.disconnect(self._cpi)
        model.disconnect(self._crd)
        model.disconnect(self._crc)

    def _on_playing_song_changed(self, *args):
        '''
          signal when a playing song changes - need to invoke a tree-refresh to ensure the user can see which source
        :param args:
        :return:
        '''
        print ("playing song changed")
        if hasattr(self.plugin, "db"): # curious crash when exiting - lets not send the queue_draw in this case
            print ("queuing")
            self.queue_draw()

    def on_renderertext_edited(self, renderer, path, new_text):
        print ("edited")

        print (path)
        print (new_text)

        self.treestore_filter[path][1].props.name = new_text

    def _traverse_rows(self, store, treeiter, new_parent_iter, depth):
        while treeiter != None:
            print (depth, store[treeiter][1])
            print (depth, store[treeiter][1].props.name)
            if isinstance(store[treeiter][1], RB.DisplayPageGroup):
                if store.iter_has_child(treeiter):
                    childiter = store.iter_children(treeiter)
                    self._traverse_rows(store, childiter, treeiter, depth)
                treeiter = store.iter_next(treeiter)
                continue

            if depth == 0:
                category_iter = self._get_category_iter(store[treeiter][1])
                leaf_iter = self.treestore.append(category_iter)
            else:
                leaf_iter = self.treestore.append(new_parent_iter)

            self.treestore[leaf_iter][1] = store[treeiter][1]
            self.treestore[leaf_iter][0] = ""
            self.treestore[leaf_iter][2] = True

            if store.iter_has_child(treeiter):
                childiter = store.iter_children(treeiter)
                self._traverse_rows(store, childiter, leaf_iter, depth + 1)
            treeiter = store.iter_next(treeiter)

    def _model_page_changed(self, model, path, page_iter):
        print (model[page_iter][1].props.name)
        print (path)

    def _model_page_inserted(self, model, page, page_iter):
        print (page)
        print (page_iter)

        parent_iter = model.iter_parent(page_iter)

        print (parent_iter)

        def find_lookup_rows(store, treeiter, page):
            while treeiter != None:

                found_page = store[treeiter][1]
                print (found_page)
                if found_page != None and found_page == page:
                    print ("found %s" % found_page.props.name)
                    return treeiter

                if store.iter_has_child(treeiter):
                    childiter = store.iter_children(treeiter)
                    ret = find_lookup_rows(store, childiter, page)

                    if ret:
                        return ret

                treeiter = store.iter_next(treeiter)

            print ("nothing found")
            return None

        # first check if we've already got the page in the model
        rootiter = self.treestore.get_iter_first()
        if find_lookup_rows(self.treestore, rootiter, page):
            return

        if (parent_iter and isinstance(model[parent_iter][1], RB.DisplayPageGroup)) or not parent_iter:
            # the parent of the inserted row is a top-level item in the display-page-model
            print ("top level")
            category_iter = self._get_category_iter(page)
            leaf_iter = self.treestore.append(category_iter)
        else:
            # the parent is another source so we need to find the iter in our model to hang it off
            print ("child level")
            searchpage = model[parent_iter][1]
            print ("####", searchpage)
            leaf_iter = find_lookup_rows(self.treestore, rootiter, searchpage)
            print ("##2", leaf_iter)
            leaf_iter = self.treestore.append(leaf_iter)


        self.treestore[leaf_iter][1] = page
        self.treestore[leaf_iter][0] = ""
        self.treestore[leaf_iter][2] = True

        self._refresh_headers()

        if "PlaylistSource" in type(page).__name__:
            # a playlist of somesort has been added - so lets put the user into edit mode
            self.edit_playlist(leaf_iter)

        self.rbtree.expand_all()

    def edit_playlist(self, leaf_iter):
        '''
           edit the playlist
        :param leaf_iter: treestore iter
        :return:
        '''
        print ("edit_playlist")
        self.text_renderer.props.editable = True
        path = self.treestore.get_path(leaf_iter)
        path = self.treestore_filter.convert_child_path_to_path(path)
        print (path)
        self.grab_focus()

        def delayed(*args):

            self.set_cursor_on_cell(path, self.tree_column, self.text_renderer, True)

        GLib.timeout_add_seconds(1, delayed, None)


    def _model_page_deleted(self, model, path):
        '''
          signal from the displaytreemodel - we dont actually know what is deleted ... just that something has been
        :param model:
        :param path:
        :return:
        '''

        # first do a reverse lookup so that we can search quicker later
        # dict of sources in the sidebar model with their treeiter
        lookup = {}
        rootiter = self.treestore.get_iter_first()

        def find_lookup_rows(store, treeiter):
            while treeiter != None:
                #if store[treeiter][0] == "":
                #    lookup[store[treeiter][1]] = treeiter

                if store[treeiter][1] != None:
                    lookup[store[treeiter][1]] = treeiter

                if store.iter_has_child(treeiter):
                    childiter = store.iter_children(treeiter)
                    find_lookup_rows(store, childiter)
                treeiter = store.iter_next(treeiter)

        find_lookup_rows(self.treestore, rootiter)

        # next iterate through the displaytreemodel - where we have a matching source, delete it from our lookup
        def find_rows(store, treeiter):
            while treeiter != None:
                if store[treeiter][1] in lookup:
                    del lookup[store[treeiter][1]]

                if store.iter_has_child(treeiter):
                    childiter = store.iter_children(treeiter)
                    find_rows(store, childiter)
                treeiter = store.iter_next(treeiter)

        rootiter = model.get_iter_first()
        find_rows(model, rootiter)

        # from what is left is the stuff to remove from our treeview (treestore)
        for source in lookup:
            self.treestore.remove(lookup[source])

        self._refresh_headers()

    def _row_click(self, widget, event):
        '''
        event called when clicking on a row
        '''
        print('_row_click')

        try:
            treepath, treecolumn, cellx, celly = widget.get_path_at_pos(event.x, event.y)
        except:
            print ("exit")
            return

        active_object = self.treestore_filter[treepath][1]
        print (active_object)

        if active_object:
            # we have a source
            self._user_clicked = True
            self.shell.props.display_page_tree.select(active_object)
            self.rbtree.expand_all()
            if self._last_click_source == active_object:
                self.text_renderer.props.editable = "PlaylistSource" in type(active_object).__name__
            else:
                self.text_renderer.props.editable = False
                self._last_click_source = active_object

        def delayed(*args):
            # save current state of each category in the treeview
            cat_vals = {}
            for category in self._category:
                path = self.treestore.get_path(self._category[category])
                if path:
                    cat_vals[category] = self.row_expanded(path)

            self.expanders=str(cat_vals)
            print (self.expanders)

        GLib.timeout_add_seconds(1, delayed)

    def _display_page_tree_selected(self, display_page_tree, page):
        '''
        signal from when a page is selected in the display-page-tree - we need to sync with our tree
        :param display_page_tree:
        :param page:
        :return:
        '''

        if self._user_clicked:
            self._user_clicked = False
            return
            
        # first do a reverse lookup so that we can search quicker later
        # dict of sources in the sidebar model with their treeiter
        lookup = {}
        rootiter = self.treestore_filter.get_iter_first()

        def find_lookup_rows(store, treeiter):
            while treeiter != None:

                if store[treeiter][1] != None:
                    lookup[store[treeiter][1]] = treeiter
                    print (store[treeiter][1].props.name)

                if store.iter_has_child(treeiter):
                    childiter = store.iter_children(treeiter)
                    find_lookup_rows(store, childiter)
                treeiter = store.iter_next(treeiter)

        find_lookup_rows(self.treestore_filter, rootiter)

        if page in lookup:
            path = self.treestore_filter.get_path(lookup[page])
            self.expand_to_path(path)
            self.set_cursor(path)

    def _set_text(self, column, renderer, model, treeiter, arg):
        source = model[treeiter][1]
        if source == None:
            renderer.props.weight = Pango.Weight.BOLD
            renderer.props.text = model[treeiter][0]
            renderer.props.visible = model[treeiter][2]
        else:
            renderer.props.visible = True
            player = self.shell.props.shell_player
            playing = player.get_playing and player.get_playing_source() == source
            renderer.props.text = source.props.name
            if playing:
                renderer.props.weight = Pango.Weight.BOLD
            else:
                renderer.props.weight = Pango.Weight.NORMAL
            renderer.props.ypad = 3

        path = model.get_path(treeiter)

        if path.get_depth() == 1:
            renderer.props.ypad = 6
            renderer.props.xpad = 3
        else:
            renderer.props.ypad = 3
            renderer.props.xpad = 0

        renderer.props.ellipsize = Pango.EllipsizeMode.END

    def _refresh_headers(self):
        treeiter = self.treestore.get_iter_first()

        while treeiter != None:
            self.treestore[treeiter][2] = self.treestore.iter_has_child(treeiter)

            treeiter = self.treestore.iter_next(treeiter)

    def _set_pixbuf(self, column, renderer, model, treeiter, arg):
        source = model[treeiter][1]
        if source == None:
            renderer.props.pixbuf = None
        else:
            ret_bool, controller = self.toolbar.is_controlled(source)

            renderer.props.gicon = controller.get_gicon(source)
            renderer.props.follow_state = True

        path = model.get_path(treeiter)
        if path.get_depth() == 2:
            renderer.props.visible = True # must be a child so show the pixbuf renderer
        else:
            renderer.props.visible = False # headers or children of child dont have pixbuf's so no renderer to display

        renderer.props.xpad = 3

    def _get_category_iter(self, source):
        ret_bool, controller = self.toolbar.is_controlled(source)

        category = AltControllerCategory.OTHER

        if ret_bool:
            category = controller.get_category()

        return self._category[category]
