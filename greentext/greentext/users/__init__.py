from datetime import datetime

from greentext.users.countries import Country


class User(object):
    def __eq__(self, other):
        if other.__class__ is self.__class__:
            return () == ()
        else:
            return NotImplemented

    def __hash__(self):
        return hash(())

    def __init__(self, response):
        self.cap_code = response.get("capcode")
        self.country = Country(response) if response.get("country") is not None else None
        self.id = response.get("id")
        self.name = response.get("name")
        self.pass_year = (
            datetime.fromtimestamp(response.get("since4pass")) if response.get("since4pass") is not None else None
        )
        self.trip_code = response.get("trip")

    def serialize(self):
        return {
            "cap_code": self.cap_code,
            "country": self.country.serialize() if self.country is not None else None,
            "id": self.id,
            "name": self.name,
            "pass_year": self.pass_year,
            "trip_code": self.trip_code,
        }
