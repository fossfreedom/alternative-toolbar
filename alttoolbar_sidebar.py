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
from gi.repository import GdkPixbuf
from gi.repository import RB
from alttoolbar_controller import AltControllerCategory

import rb


class AltToolbarSidebar(Gtk.Grid):
    def __init__(self, toolbar):
        '''
        Initialises the object.
        '''
        super(AltToolbarSidebar, self).__init__()

        self.shell = toolbar.shell
        self.toolbar = toolbar
        self.plugin = toolbar.plugin

        self._category = {}

        # title, source, visible
        self.treestore = Gtk.TreeStore.new([str, GObject.Object, bool])
        self.treestore_filter = self.treestore.filter_new(root=None)
        self.treestore_filter.set_visible_column(2)

        self.treeview = Gtk.TreeView.new_with_model(self.treestore_filter)
        context = self.treeview.get_style_context()
        context.add_class(Gtk.STYLE_CLASS_SIDEBAR)
        self.treeview.set_headers_visible(False)

        self.scrolledwindow = Gtk.ScrolledWindow.new()
        self.scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scrolledwindow.set_hexpand(True)
        self.scrolledwindow.set_vexpand(True)
        self.add(self.treeview)
        self.attach(self.scrolledwindow, 0, 0, 1, 1)


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

            # add display-page-model to our model
            self._traverse_rows(model, rootiter, None, depth)

            # next add playlists to our model

            playlists = self.shell.props.playlist_manager.get_playlists()
            playlist_iter = self._category[AltControllerCategory.PLAYLIST]
            for playlist in playlists:
                local = self.treestore.append(playlist_iter)
                self.treestore[local] = ["", playlist, True]

            # switch on/off headers depending upon what's in the model
            self._refresh_headers()

            # tidy up syncing by connecting signals
            self._connect_signals()

            self.treeview.expand_row(self.treestore.get_path(self._category[AltControllerCategory.LOCAL]), True)
            return False

        GLib.timeout_add_seconds(1, delayed)

        column = Gtk.TreeViewColumn.new()

        pixbuf_renderer = Gtk.CellRendererPixbuf()
        column.pack_start(pixbuf_renderer, False)
        renderer = Gtk.CellRendererText()
        column.pack_start(renderer, False)

        column.set_cell_data_func(pixbuf_renderer, self._set_pixbuf)
        column.set_cell_data_func(renderer, self._set_text)

        self.treeview.append_column(column)
        self.treeview.show_all()


    def _connect_signals(self):
        # display_page_model signals to keep the sidebar model in sync
        model = self.shell.props.display_page_model
        model.connect('row-inserted', self._model_page_inserted)
        model.connect('row-deleted', self._model_page_deleted)
        model.connect('row-changed', self._model_page_changed)

        # when we click on the sidebar - need to keep the display_page_tree in sync
        self.treeview.connect('button-press-event', self._row_click)
        # and visa versa
        self.shell.props.display_page_tree.connect('selected', self._display_page_tree_selected)

    def _traverse_rows(self, store, treeiter, new_parent_iter, depth):
        while treeiter != None:
            print (depth, store[treeiter][1])
            print (depth, store[treeiter][1].props.name)
            if isinstance(store[treeiter][1], RB.DisplayPageGroup):
                treeiter = store.iter_children(treeiter)
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
        print (model[page_iter])
        print (path)

    def _model_page_inserted(self, model, path, page_iter):
        print (path)
        print (page_iter)

        page = model[path][1]

        category_iter = self._get_category_iter(page)
        leaf_iter = self.treestore.append(category_iter)
        self.treestore[leaf_iter][1] = page
        self.treestore[leaf_iter][0] = ""
        self.treestore[leaf_iter][2] = True

        self._refresh_headers()

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

        #print (lookup)

        # next iterate through the displaytreemodel - where we have a matching source, delete it from our lookup
        def find_rows(store, treeiter):
            while treeiter != None:
                #print (str(store[treeiter][:]))
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
            return

        active_object = self.treestore_filter[treepath][1]

        if active_object:
            # we have a source
            self.shell.props.display_page_tree.select(active_object)

    def _display_page_tree_selected(self, display_page_tree, page):
        '''
        signal from when a page is selected in the display-page-tree - we need to sync with our tree
        :param display_page_tree:
        :param page:
        :return:
        '''

        # first do a reverse lookup so that we can search quicker later
        # dict of sources in the sidebar model with their treeiter
        lookup = {}
        rootiter = self.treestore_filter.get_iter_first()

        def find_lookup_rows(store, treeiter):
            while treeiter != None:

                if store[treeiter][1] != None:
                    lookup[store[treeiter][1]] = treeiter

                if store.iter_has_child(treeiter):
                    childiter = store.iter_children(treeiter)
                    find_lookup_rows(store, childiter)
                treeiter = store.iter_next(treeiter)

        find_lookup_rows(self.treestore_filter, rootiter)

        if page in lookup:
            path = self.treestore_filter.get_path(lookup[page])
            self.treeview.expand_to_path(path)
            self.treeview.set_cursor(path)

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

            #renderer.props.pixbuf = controller.get_icon_pixbuf(source)
            renderer.props.gicon = controller.get_gicon(source)

        path = model.get_path(treeiter)
        if path.get_depth() == 1:
            renderer.props.visible = False # headers dont have pixbuf's so no renderer to display
        else:
            renderer.props.visible = True # must be a child so show the pixbuf renderer

        renderer.props.xpad = 3

    def _get_category_iter(self, source):
        ret_bool, controller = self.toolbar.is_controlled(source)

        category = AltControllerCategory.OTHER

        if ret_bool:
            category = controller.get_category()

        return self._category[category]
