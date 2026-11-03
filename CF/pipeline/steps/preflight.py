from .step import Step


class Preflight(Step):
    def process(self, data, inputs, utils):
        utils.create_dirs()
        return data
