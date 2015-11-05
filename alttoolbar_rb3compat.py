# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# IMPORTANT - WHILST THIS MODULE IS USED BY SEVERAL OTHER PLUGINS
# THE MASTER AND MOST UP-TO-DATE IS FOUND IN THE COVERART BROWSER
# PLUGIN - https://github.com/fossfreedom/coverart-browser
# PLEASE SUBMIT CHANGES BACK TO HELP EXPAND THIS API
#
# Copyright (C) 2012-2015 - fossfreedom
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
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

import sys
import xml.etree.ElementTree as ET

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import RB

import rb


def gtk_version():
    """
    returns float of the major and minor parts of the GTK version
    e.g. return float(3.10)
    """

    return float(str(Gtk.get_major_version()) + "." +
                 str(Gtk.get_minor_version()))


def pygobject_version():
    """
    returns float of the major and minor parts of a pygobject version 
    e.g. version (3, 9, 5) return float(3.9)
    """
    to_number = lambda t: ".".join(str(v) for v in t)

    str_version = to_number(GObject.pygobject_version)

    return float(str_version.rsplit('.', 1)[0])


def compare_pygobject_version(version):
    """
    return True if version is less than pygobject_version
    i.e. 3.9 < 3.11
    """
    to_number = lambda t: ".".join(str(v) for v in t)

    str_version = to_number(GObject.pygobject_version)

    split = str_version.rsplit('.', 2)
    split_compare = version.rsplit('.', 2)

    if int(split_compare[0]) < int(split[0]):
        return True

    if int(split_compare[1]) < int(split[1]):
        return True

    return False


PYVER = sys.version_info[0]

if PYVER >= 3:
    import urllib.request
    import urllib.parse
    import urllib.error
else:
    import urllib
    from urlparse import urlparse as rb2urlparse

if PYVER >= 3:
    import http.client
    # pyflakes doesnt like python2 unicode so lets give it something
    # to chew on

    def unicode(a, b):
        return (a, b)

else:
    import httplib


def responses():
    if PYVER >= 3:
        return http.client.responses
    else:
        return httplib.responses


def unicodestr(param, charset):
    if PYVER >= 3:
        return param  # str(param, charset)
    else:
        return unicode(param, charset)


def unicodeencode(param, charset):
    if PYVER >= 3:
        return param  # str(param).encode(charset)
    else:
        return unicode(param).encode(charset)


def unicodedecode(param, charset):
    if PYVER >= 3:
        return param
    else:
        return param.decode(charset)


def urlparse(uri):
    if PYVER >= 3:
        return urllib.parse.urlparse(uri)
    else:
        return rb2urlparse(uri)


def url2pathname(url):
    if PYVER >= 3:
        return urllib.request.url2pathname(url)
    else:
        return urllib.url2pathname(url)


def urlopen(filename):
    if PYVER >= 3:
        return urllib.request.urlopen(filename)
    else:
        return urllib.urlopen(filename)


def pathname2url(filename):
    if PYVER >= 3:
        return urllib.request.pathname2url(filename)
    else:
        return urllib.pathname2url(filename)


def unquote(uri):
    if PYVER >= 3:
        return urllib.parse.unquote(uri)
    else:
        return urllib.unquote(uri)


def quote(uri, safe=None):
    if PYVER >= 3:
        if safe:
            return urllib.parse.quote(uri, safe=safe)
        else:
            return urllib.parse.quote(uri)
    else:
        if safe:
            return urllib.quote(uri, safe=safe)
        else:
            return urllib.quote(uri)


def quote_plus(uri):
    if PYVER >= 3:
        return urllib.parse.quote_plus(uri)
    else:
        return urllib.quote_plus(uri)


def is_rb3(*args):
    if hasattr(RB.Shell.props, 'ui_manager'):
        return False
    else:
        return True


class Menu(GObject.Object):
    """
    Menu object used to create window popup menus
    """
    __gsignals__ = {
        'pre-popup': (GObject.SIGNAL_RUN_LAST, None, ())
    }

    def __init__(self, plugin, shell):
        """
        Initializes the menu.
        """
        super(Menu, self).__init__()
        self.plugin = plugin
        self.shell = shell
        self._unique_num = 0

        self._rbmenu_items = {}
        self._rbmenu_objects = {}

    def add_menu_item(self, menubar, section_name, action):
        """
        add a new menu item to the popup
        :param menubar: `str` is the name GtkMenu (or ignored for RB2.99+)
        :param section_name: `str` is the name of the section to add the item
        to (RB2.99+)
        :param action: `Action`  to associate with the menu item
        """
        return self.insert_menu_item(menubar, section_name, -1, action)

    def insert_menu_item(self, menubar, section_name, position, action):
        """
        add a new menu item to the popup
        :param menubar: `str` is the name GtkMenu (or ignored for RB2.99+)
        :param section_name: `str` is the name of the section to add the item
        to (RB2.99+)
        :param position: `int` position to add to GtkMenu (ignored for RB2.99+)
        :param action: `Action`  to associate with the menu item
        """
        label = action.label

        if is_rb3(self.shell):
            app = self.shell.props.application
            item = Gio.MenuItem()
            action.associate_menuitem(item)
            item.set_label(label)

            if not section_name in self._rbmenu_items:
                self._rbmenu_items[section_name] = []
            self._rbmenu_items[section_name].append(label)

            app.add_plugin_menu_item(section_name, label, item)
        else:
            item = Gtk.MenuItem(label=label)
            action.associate_menuitem(item)
            self._rbmenu_items[label] = item
            bar = self.get_menu_object(menubar)

            if position == -1:
                bar.append(item)
            else:
                bar.insert(item, position)
            bar.show_all()
            uim = self.shell.props.ui_manager
            uim.ensure_update()

        return item

    def insert_separator(self, menubar, at_position):
        """
        add a separator to the popup (only required for RB2.98 and earlier)
        :param menubar: `str` is the name GtkMenu (or ignored for RB2.99+)
        :param position: `int` position to add to GtkMenu (ignored for RB2.99+)
        """
        if not is_rb3(self.shell):
            menu_item = Gtk.SeparatorMenuItem().new()
            menu_item.set_visible(True)
            self._rbmenu_items['separator' + str(self._unique_num)] = menu_item
            self._unique_num = self._unique_num + 1
            bar = self.get_menu_object(menubar)
            bar.insert(menu_item, at_position)
            bar.show_all()
            uim = self.shell.props.ui_manager
            uim.ensure_update()

    def remove_menu_items(self, menubar, section_name):
        """
        utility function to remove all menuitems associated with the menu
        section
        :param menubar: `str` is the name of the GtkMenu containing the menu
        items (ignored for RB2.99+)
        :param section_name: `str` is the name of the section containing the
        menu items (for RB2.99+ only)
        """
        if is_rb3(self.shell):
            if not section_name in self._rbmenu_items:
                return

            app = self.shell.props.application

            for menu_item in self._rbmenu_items[section_name]:
                app.remove_plugin_menu_item(section_name, menu_item)

            if self._rbmenu_items[section_name]:
                del self._rbmenu_items[section_name][:]

        else:

            if not self._rbmenu_items:
                return

            uim = self.shell.props.ui_manager
            bar = self.get_menu_object(menubar)

            for menu_item in self._rbmenu_items:
                bar.remove(self._rbmenu_items[menu_item])

            bar.show_all()
            uim.ensure_update()

    def load_from_file(self, rb2_ui_filename, rb3_ui_filename):
        """
        utility function to load the menu structure
        :param rb2_ui_filename: `str` RB2.98 and below UI file
        :param rb3_ui_filename: `str` RB2.99 and higher UI file
        """
        self.builder = Gtk.Builder()
        try:
            from coverart_browser_prefs import CoverLocale

            cl = CoverLocale()

            self.builder.set_translation_domain(cl.Locale.LOCALE_DOMAIN)
        except:
            pass

        if is_rb3(self.shell):
            ui_filename = rb3_ui_filename
        else:
            ui_filename = rb2_ui_filename

        self.ui_filename = ui_filename

        self.builder.add_from_file(rb.find_plugin_file(self.plugin,
                                                       ui_filename))

    def _connect_rb3_signals(self, signals):
        def _menu_connect(action_name, func):
            action = Gio.SimpleAction(name=action_name)
            action.connect('activate', func)
            action.set_enabled(True)
            self.shell.props.window.add_action(action)

        for key, value in signals.items():
            _menu_connect(key, value)

    def _connect_rb2_signals(self, signals):
        def _menu_connect(menu_item_name, func):
            menu_item = self.get_menu_object(menu_item_name)
            menu_item.connect('activate', func)

        for key, value in signals.items():
            _menu_connect(key, value)

    def connect_signals(self, signals):
        """
        connect all signal handlers with their menuitem counterparts
        :param signals: `dict` key is the name of the menuitem 
             and value is the function callback when the menu is activated
        """
        if is_rb3(self.shell):
            self._connect_rb3_signals(signals)
        else:
            self._connect_rb2_signals(signals)

    def get_gtkmenu(self, source, popup_name):
        """
        utility function to obtain the GtkMenu from the menu UI file
        :param popup_name: `str` is the name menu-id in the UI file
        """
        if popup_name in self._rbmenu_objects:
            return self._rbmenu_objects[popup_name]
        item = self.builder.get_object(popup_name)

        if is_rb3(self.shell):
            app = self.shell.props.application
            app.link_shared_menus(item)
            popup_menu = Gtk.Menu.new_from_model(item)
            popup_menu.attach_to_widget(source, None)
        else:
            popup_menu = item

        self._rbmenu_objects[popup_name] = popup_menu

        return popup_menu

    def get_menu_object(self, menu_name_or_link):
        """
        utility function returns the GtkMenuItem/Gio.MenuItem
        :param menu_name_or_link: `str` to search for in the UI file
        """
        if menu_name_or_link in self._rbmenu_objects:
            return self._rbmenu_objects[menu_name_or_link]
        item = self.builder.get_object(menu_name_or_link)
        if is_rb3(self.shell):
            if item:
                popup_menu = item
            else:
                app = self.shell.props.application
                popup_menu = app.get_plugin_menu(menu_name_or_link)
        else:
            popup_menu = item
        print(menu_name_or_link)
        self._rbmenu_objects[menu_name_or_link] = popup_menu

        return popup_menu

    def set_sensitive(self, menu_or_action_item, enable):
        """
        utility function to enable/disable a menu-item
        :param menu_or_action_item: `GtkMenuItem` or `Gio.SimpleAction`
           that is to be enabled/disabled
        :param enable: `bool` value to enable/disable
        """

        if is_rb3(self.shell):
            item = self.shell.props.window.lookup_action(menu_or_action_item)
            item.set_enabled(enable)
        else:
            item = self.get_menu_object(menu_or_action_item)
            item.set_sensitive(enable)

    def popup(self, source, menu_name, button, time):
        """
        utility function to show the popup menu
        """
        self.emit('pre-popup')
        menu = self.get_gtkmenu(source, menu_name)
        menu.popup(None, None, None, None, button, time)


class ActionGroup(object):
    """
    container for all Actions used to associate with menu items
    """

    # action_state
    STANDARD = 0
    TOGGLE = 1

    def __init__(self, shell, group_name):
        """
        constructor
        :param shell: `RBShell`
        :param group_name: `str` unique name for the object to create
        """
        self.group_name = group_name
        self.shell = shell

        self._actions = {}

        if is_rb3(self.shell):
            self.actiongroup = Gio.SimpleActionGroup()
        else:
            self.actiongroup = Gtk.ActionGroup(group_name)
            uim = self.shell.props.ui_manager
            uim.insert_action_group(self.actiongroup)

    @property
    def name(self):
        return self.group_name

    def remove_actions(self):
        """
        utility function to remove all actions associated with the ActionGroup
        """
        for action in self.actiongroup.list_actions():
            self.actiongroup.remove_action(action)

    def get_action(self, action_name):
        """
        utility function to obtain the Action from the ActionGroup

        :param action_name: `str` is the Action unique name
        """
        return self._actions[action_name]

    def add_action_with_accel(self, func, action_name, accel, **args):
        """
        Creates an Action with an accelerator and adds it to the ActionGroup

        :param func: function callback used when user activates the action
        :param action_name: `str` unique name to associate with an action
        :param accel: `str` accelerator
        :param args: dict of arguments - this is passed to the function
        callback

        Notes: 
        see notes for add_action
        """
        args['accel'] = accel
        return self.add_action(func, action_name, **args)

    def add_action(self, func, action_name, **args):
        """
        Creates an Action and adds it to the ActionGroup

        :param func: function callback used when user activates the action
        :param action_name: `str` unique name to associate with an action
        :param args: dict of arguments - this is passed to the function
        callback

        Notes: 
        key value of "label" is the visual menu label to display
        key value of "action_type" is the RB2.99 Gio.Action type
        ("win" or "app") by default it assumes all actions are "win" type
        key value of "action_state" determines what action state to create
        """
        if 'label' in args:
            label = args['label']
        else:
            label = action_name

        if 'accel' in args:
            accel = args['accel']
        else:
            accel = None

        state = ActionGroup.STANDARD
        if 'action_state' in args:
            state = args['action_state']

        if is_rb3(self.shell):
            if state == ActionGroup.TOGGLE:
                action = Gio.SimpleAction.new_stateful(action_name, None,
                                                       GLib.Variant('b',
                                                                    False))
            else:
                action = Gio.SimpleAction.new(action_name, None)

            action_type = 'win'
            if 'action_type' in args:
                if args['action_type'] == 'app':
                    action_type = 'app'

            app = Gio.Application.get_default()

            if action_type == 'app':
                app.add_action(action)
            else:
                self.shell.props.window.add_action(action)
                self.actiongroup.add_action(action)

            if accel:
                app.add_accelerator(accel, action_type + "." + action_name,
                                    None)
        else:
            if 'stock_id' in args:
                stock_id = args['stock_id']
            else:
                stock_id = Gtk.STOCK_CLEAR

            if state == ActionGroup.TOGGLE:
                action = Gtk.ToggleAction(label=label,
                                          name=action_name,
                                          tooltip='', stock_id=stock_id)
            else:
                action = Gtk.Action(label=label,
                                    name=action_name,
                                    tooltip='', stock_id=stock_id)

            if accel:
                self.actiongroup.add_action_with_accel(action, accel)
            else:
                self.actiongroup.add_action(action)

        act = Action(self.shell, action)
        act.connect('activate', func, args)

        act.label = label
        act.accel = accel

        self._actions[action_name] = act

        return act


class ApplicationShell(object):
    """
    Unique class that mirrors RB.Application & RB.Shell menu functionality
    """
    # storage for the instance reference
    __instance = None

    class __impl:
        """ Implementation of the singleton interface """

        def __init__(self, shell):
            self.shell = shell

            if is_rb3(self.shell):
                self._uids = {}
            else:
                self._uids = []

            self._action_groups = {}

        def insert_action_group(self, action_group):
            """
            Adds an ActionGroup to the ApplicationShell

            :param action_group: `ActionGroup` to add
            """
            self._action_groups[action_group.name] = action_group

        def lookup_action(self, action_group_name, action_name,
                          action_type='app'):
            """
            looks up (finds) an action created by another plugin.
            If found returns an Action or None if no matching Action.

            :param action_group_name: `str` is the Gtk.ActionGroup name
            (ignored for RB2.99+)
            :param action_name: `str` unique name for the action to look for
            :param action_type: `str` RB2.99+ action type ("win" or "app")
            """

            if is_rb3(self.shell):
                if action_type == "app":
                    action = \
                        self.shell.props.application.lookup_action(action_name)
                else:
                    action = self.shell.props.window.lookup_action(action_name)
            else:
                uim = self.shell.props.ui_manager
                ui_actiongroups = uim.get_action_groups()

                actiongroup = None
                for actiongroup in ui_actiongroups:
                    if actiongroup.get_name() == action_group_name:
                        break

                action = None
                if actiongroup:
                    action = actiongroup.get_action(action_name)

            if action:
                return Action(self.shell, action)
            else:
                return None

        def add_app_menuitems(self, ui_string, group_name, menu='tools'):
            """
            utility function to add application menu items.

            For RB2.99 all application menu items are added to the "tools"
            section of the application menu. All Actions are assumed to be of
            action_type "app".

            For RB2.98 or less, it is added however the UI_MANAGER string
            is defined.

            :param ui_string: `str` is the Gtk UI definition.  There is not an
            equivalent UI definition in RB2.99 but we can parse out menu items
            since this string is in XML format

            :param group_name: `str` unique name of the ActionGroup to add menu
            items to
            :param menu: `str` RB2.99 menu section to add to - nominally either
              'tools' or 'view'
            """
            if is_rb3(self.shell):
                root = ET.fromstring(ui_string)
                for elem in root.findall(".//menuitem"):
                    action_name = elem.attrib['action']

                    group = self._action_groups[group_name]
                    act = group.get_action(action_name)

                    item = Gio.MenuItem()
                    item.set_detailed_action('app.' + action_name)
                    item.set_label(act.label)
                    item.set_attribute_value("accel", GLib.Variant("s",
                                                                   act.accel))
                    app = Gio.Application.get_default()
                    index = menu + action_name
                    app.add_plugin_menu_item(menu,
                                             index, item)
                    self._uids[index] = menu
            else:
                uim = self.shell.props.ui_manager
                self._uids.append(uim.add_ui_from_string(ui_string))
                uim.ensure_update()

        def add_browser_menuitems(self, ui_string, group_name):
            """
            utility function to add popup menu items to existing browser popups

            For RB2.99 all menu items are are assumed to be of action_type
            "win".

            For RB2.98 or less, it is added however the UI_MANAGER string
            is defined.

            :param ui_string: `str` is the Gtk UI definition.  There is not an
            equivalent UI definition in RB2.99 but we can parse out menu items
            since this string is in XML format

            :param group_name: `str` unique name of the ActionGroup to add menu
            items to
            """
            if is_rb3(self.shell):
                root = ET.fromstring(ui_string)
                for elem in root.findall("./popup"):
                    popup_name = elem.attrib['name']

                    menuelem = elem.find('.//menuitem')
                    action_name = menuelem.attrib['action']

                    group = self._action_groups[group_name]
                    act = group.get_action(action_name)

                    item = Gio.MenuItem()
                    item.set_detailed_action('win.' + action_name)
                    item.set_label(act.label)
                    app = Gio.Application.get_default()

                    if popup_name == 'QueuePlaylistViewPopup':
                        plugin_type = 'queue-popup'
                    elif popup_name == 'BrowserSourceViewPopup':
                        plugin_type = 'browser-popup'
                    elif popup_name == 'PlaylistViewPopup':
                        plugin_type = 'playlist-popup'
                    elif popup_name == 'PodcastViewPopup':
                        plugin_type = 'podcast-episode-popup'
                    else:
                        print("unknown type %s" % plugin_type)

                    index = plugin_type + action_name
                    app.add_plugin_menu_item(plugin_type, index, item)
                    self._uids[index] = plugin_type
            else:
                uim = self.shell.props.ui_manager
                self._uids.append(uim.add_ui_from_string(ui_string))
                uim.ensure_update()

        def cleanup(self):
            """
            utility remove any menuitems created.
            """
            if is_rb3(self.shell):
                for uid in self._uids:
                    Gio.Application.get_default().remove_plugin_menu_item(
                        self._uids[uid], uid)
            else:
                uim = self.shell.props.ui_manager
                for uid in self._uids:
                    uim.remove_ui(uid)
                uim.ensure_update()

    def __init__(self, shell):
        """ Create singleton instance """
        # Check whether we already have an instance
        if ApplicationShell.__instance is None:
            # Create and remember instance
            ApplicationShell.__instance = ApplicationShell.__impl(shell)

        # Store instance reference as the only member in the handle
        self.__dict__['_ApplicationShell__instance'] = \
            ApplicationShell.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)


class Action(object):
    """
    class that wraps around either a Gio.Action or a Gtk.Action
    """

    def __init__(self, shell, action):
        """
        constructor.

        :param shell: `RBShell`
        :param action: `Gio.Action` or `Gtk.Action`
        """
        self.shell = shell
        self.action = action

        self._label = ''
        self._accel = ''
        self._current_state = False
        self._do_update_state = True

    def connect(self, address, func, args):
        self._connect_func = func
        self._connect_args = args

        if address == 'activate':
            func = self._activate

        if is_rb3(self.shell):
            self.action.connect(address, func, args)
        else:
            self.action.connect(address, func, None, args)

    def _activate(self, action, *args):
        if self._do_update_state:
            self._current_state = not self._current_state
            self.set_state(self._current_state)

        self._connect_func(action, None, self._connect_args)

    @property
    def label(self):
        """
        get the menu label associated with the Action

        for RB2.99+ actions dont have menu labels so this is managed
        manually
        """
        if not is_rb3(self.shell):
            return self.action.get_label()
        else:
            return self._label

    @label.setter
    def label(self, new_label):
        if not is_rb3(self.shell):
            self.action.set_label(new_label)

        self._label = new_label

    @property
    def accel(self):
        """
        get the accelerator associated with the Action
        """
        return self._accel

    @accel.setter
    def accel(self, new_accelerator):
        if new_accelerator:
            self._accel = new_accelerator
        else:
            self._accel = ''

    def get_sensitive(self):
        """
        get the sensitivity (enabled/disabled) state of the Action

        returns boolean
        """
        if is_rb3(self.shell):
            return self.action.get_enabled()
        else:
            return self.action.get_sensitive()

    def set_state(self, value):
        """
        set the state of a stateful action - this is applicable only
        to RB2.99+
        """
        if is_rb3(self.shell) and self.action.props.state_type:
            self.action.change_state(GLib.Variant('b', value))

    def activate(self):
        """
        invokes the activate signal for the action
        """
        if is_rb3(self.shell):
            self.action.activate(None)
        else:
            self.action.activate()

    def set_active(self, value):
        """
        activate or deactivate a stateful action signal
        For consistency with earlier RB versions, this will fire the
        activate signal for the action

        :param value: `boolean` state value
        """

        if is_rb3(self.shell):
            self.action.change_state(GLib.Variant('b', value))
            self._current_state = value
            self._do_update_state = False
            self.activate()
            self._do_update_state = True
        else:
            self.action.set_active(value)

    def get_active(self):
        """
        get the state of the action

        returns `boolean` state value
        """
        if is_rb3(self.shell):
            returnval = self._current_state
        else:
            returnval = self.action.get_active()

        return returnval

    def associate_menuitem(self, menuitem):
        """
        links a menu with the action

        """
        if is_rb3(self.shell):
            menuitem.set_detailed_action('win.' + self.action.get_name())
        else:
            menuitem.set_related_action(self.action)
