# -*- coding: latin-1 -*-


import weakref


_model_views = weakref.WeakKeyDictionary()

from .properties import overridable_property


class Model(object):
    views = overridable_property("views", "List of objects observing this model. Do not modify directly.")

    def destroy(self):
        self.notify_views("model_destroyed")
        for view in self.views[:]:
            self.remove_view(view)
            # self._call_if_present(view, 'model_destroyed', self)

    def get_views(self):
        views = _model_views.get(self)
        if views is None:
            views = []
            _model_views[self] = views
        return views

    def add_view(self, view):
        views = self.views
        if view not in views:
            views.append(view)
            self._call_if_present(view, "add_model", self)

    def remove_view(self, view):
        views = self.views
        if view in views:
            views.remove(view)
            self._call_if_present(view, "remove_model", self)

    def notify_views(self, message="model_changed", *args, **kwds):
        for view in self.views:
            if not self._call_if_present(view, message, self, *args, **kwds):
                self._call_if_present(view, "model_changed", self)

    def _call_if_present(self, obj, method_name, *args, **kwds):
        method = getattr(obj, method_name, None)
        if method:
            method(*args, **kwds)
            return 1
        else:
            return 0
