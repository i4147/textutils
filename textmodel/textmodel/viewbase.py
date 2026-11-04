from .properties import overridable_property


class ViewBase(object):
    models = overridable_property("models", "List of Models being observed. Do not modify directly.")

    model = overridable_property("model", "Convenience property for views which observe only one Model.")

    def __init__(self):
        self._models = []

    def destroy(self):
        for m in self._models[:]:
            self.remove_model(m)

    def get_model(self):
        models = self._models
        if models:
            return self._models[0]
        else:
            return None

    def get_models(self):
        return self._models

    def set_model(self, new_model):
        models = self._models
        if not (len(models) == 1 and models[0] == new_model):
            for old_model in models[:]:
                self.remove_model(old_model)
            if new_model is not None:
                self.add_model(new_model)

    def add_model(self, model):
        if model not in self._models:
            self._models.append(model)
            model.add_view(self)

    def remove_model(self, model):
        if model in self._models:
            self._models.remove(model)
            model.remove_view(self)

    def model_changed(self, model, *args, **kwds):
        pass

    def model_destroyed(self, model):
        pass
