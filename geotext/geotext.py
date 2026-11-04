# -*- coding: utf-8 -*-


from collections import namedtuple, Counter, OrderedDict
import re
import os
import io

_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data_path(path):
    return os.path.join(_ROOT, "data", path)


def read_table(filename, usecols=(0, 1), sep="\t", comment="#", encoding="utf-8", skip=0):

    with io.open(filename, "r", encoding=encoding) as f:
        for _ in range(skip):
            next(f)

        lines = (line for line in f if not line.startswith(comment))

        d = dict()
        for line in lines:
            columns = line.split(sep)
            key = columns[usecols[0]].lower()
            value = columns[usecols[1]].rstrip("\n")
            d[key] = value
    return d


def build_index():

    nationalities = read_table(get_data_path("nationalities.txt"), sep=":")

    countries = read_table(get_data_path("countryInfo.txt"), usecols=[4, 0], skip=1)

    cities = read_table(get_data_path("cities15000.txt"), usecols=[1, 8])

    city_patches = read_table(get_data_path("citypatches.txt"))
    cities.update(city_patches)

    Index = namedtuple("Index", "nationalities cities countries")
    return Index(nationalities, cities, countries)


class GeoText(object):
    index = build_index()

    def __init__(self, text, country=None):
        city_regex = r"[A-ZÀ-Ú]+[a-zà-ú]+[ \-]?(?:d[a-u].)?(?:[A-ZÀ-Ú]+[a-zà-ú]+)*"
        candidates = re.findall(city_regex, text)
        candidates = [candidate.strip() for candidate in candidates]
        self.countries = [each for each in candidates if each.lower() in self.index.countries]
        self.cities = [
            each
            for each in candidates
            if each.lower() in self.index.cities and each.lower() not in self.index.countries
        ]
        if country is not None:
            self.cities = [city for city in self.cities if self.index.cities[city.lower()] == country]

        self.nationalities = [each for each in candidates if each.lower() in self.index.nationalities]

        self.country_mentions = [self.index.countries[country.lower()] for country in self.countries]
        self.country_mentions.extend([self.index.cities[city.lower()] for city in self.cities])
        self.country_mentions.extend([
            self.index.nationalities[nationality.lower()] for nationality in self.nationalities
        ])
        self.country_mentions = OrderedDict(Counter(self.country_mentions).most_common())


if __name__ == "__main__":
    print(GeoText("In a filing with the Hong Kong bourse, the Chinese cement producer said ...").countries)
