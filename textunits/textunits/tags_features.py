from textunits import TextUnits
import string


class TagFeaturesCreator:
    def __init__(self, text_units: TextUnits):
        assert isinstance(text_units, TextUnits), "text_unit needs to be a TextUnits"
        self.text_units = text_units
        self.units = text_units.units

    @property
    def get_units(self):
        return self.units

    def unit_get_text(self, unit):
        text = " ".join(unit.text.split())

        return text.translate(text.maketrans("", "", string.punctuation))

    def __feature_methods__(self):

        methods_list = []
        for defined in dir(self):
            if defined.startswith("unit_"):
                methods_list.append(defined)
        return methods_list

    def create_features(self):

        feature_methods = self.__feature_methods__()
        units = self.get_units
        features = {}

        for method in feature_methods:
            # print(method)
            feature_name = method.split("unit_")[-1]
            inclass_method_callback = lambda unit: getattr(self, method)(unit)
            res = list(map(inclass_method_callback, units))

            features[feature_name] = res

        return features
