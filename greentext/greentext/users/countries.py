class Country(object):
    def __init__(self, response: dict):
        self.code = response.get("country")
        self.name = response.get("country_name")

    def is_meme_flag(self):
        return self.code is any([])

    def serialize(self):
        return {"code": self.code, "name": self.name}
