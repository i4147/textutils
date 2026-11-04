from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# from builtins import int

from .uierrors import UIValueError, UITypeError, UICallbackError, UIErrorWrapper
from .uielements import user_input_date, user_input_value, user_input_list, user_input_yn, user_onoff_list


class _MenuItem(object):
    def __init__(self, name_in, callback_in):
        self.name = name_in
        self.callback = callback_in


class _CallBack(object):
    def __init__(self, fxn, parent_menu, *args):
        self.return_fxn = fxn
        self.parent = parent_menu
        self.extra_fxns = args

    def execute(self):
        for fxn in self.extra_fxns:
            fxn()
        return self.return_fxn()

    def get_menu_hierarchy(self):
        hierarchy = []
        next_menu = self.parent
        while next_menu is not None:
            hierarchy.insert(0, next_menu.name)

        return hierarchy


class Program(object):
    def __init__(self, main_menu):
        if type(main_menu) is not Menu:
            UIErrorWrapper.raise_error(UITypeError("main_menu must be an instance of Menu"))
        self.next_callback = _CallBack(main_menu.interact, None)
        self.main_loop()

    def main_loop(self):
        while True:
            new_callback = self.next_callback.execute()
            if type(new_callback) is not _CallBack:
                UIErrorWrapper.raise_error(UICallbackError(self.next_callback))
            else:
                self.next_callback = new_callback


class Menu(object):
    def __init__(self, menu_name, parent_in=None):
        self.name = menu_name
        self.parent = parent_in
        self.menu_items = []
        if self.parent is None:
            self._add_item("Quit", self._quit_program)
        else:
            self._add_item("Up one level", self._up_one_level)

    def interact(self):
        ind = user_input_list("=== {0} ===".format(self.name), self.__item_names(), returntype="index")
        return self.menu_items[ind].callback

    def _add_item(self, name, callback):
        if type(name) is not str:
            UIErrorWrapper.raise_error(UITypeError("name must be a string"))
        if not callable(callback) and not isinstance(callback, _CallBack):
            UIErrorWrapper.raise_error(
                UITypeError("callback must be a function or an instance of textui.uibuilder.Callback")
            )

        if isinstance(callback, _CallBack):
            callback_inst = callback
        else:
            callback_inst = _CallBack(callback, self)
        item = _MenuItem(name, callback_inst)
        self.menu_items.insert(-1, item)

    def add_submenu(self, submenu_title, menu_item_name=None):
        if not isinstance(submenu_title, str):
            UIErrorWrapper.raise_error("submenu_title must be a string")

        if menu_item_name is None:
            menu_item_name = submenu_title
        elif not isinstance(menu_item_name, str):
            UIErrorWrapper.raise_error("menu_item_name must be a string, if given")

        smenu = Menu(submenu_title, self)
        self._add_item(menu_item_name, smenu.interact)
        return smenu

    def attach_submenu(self, submenu, menu_item_name=None):
        if not isinstance(submenu, Menu):
            UIErrorWrapper.raise_error(TypeError("submenu must be an instance of textui.uibuilder.Menu"))
        if menu_item_name is None:
            menu_item_name = submenu.name
        elif not isinstance(menu_item_name, str):
            UIErrorWrapper.raise_error(TypeError("menu_item_name must be a string"))

        if submenu.parent is not None:
            UIErrorWrapper.warn(
                'While attaching menu "{0}" to "{1}": {0} already has a parent which will be overwritten'.format(
                    submenu.name, self.name
                )
            )
        submenu.parent = self
        self._add_item(menu_item_name, submenu.interact)

    def attach_custom_fxn(self, menu_item_name, callback_fxn):
        if not isinstance(menu_item_name, str):
            UIErrorWrapper.raise_error(TypeError("menu_item_name must be a string"))
        if not callable(callback_fxn):
            UIErrorWrapper.raise_error(TypeError("callback_fxn must be a function"))

        self._add_item(menu_item_name, _CallBack(self.interact, self, callback_fxn))

    def __item_names(self):
        return [item.name for item in self.menu_items]

    def _up_one_level(self):
        return _CallBack(self.parent.interact, self)

    def _quit_program(self):
        exit(0)
