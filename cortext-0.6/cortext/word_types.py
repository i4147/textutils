import flickrapi
import urllib
import urllib.request
import urllib.parse
import base64
import json


class WordType:
    def extract_data(self, api_config=None):
        return self


class WordWithImage:
    def __init__(self, word, image_url=None):
        self.word = word
        self.image_url = image_url

    def extract_data(self, api_config):
        f = flickrapi.FlickrAPI(api_config["FLICKR_KEY"], api_config["FLICKR_SECRET"], format="parsed-json")
        photos = f.photos.search(text=self.word, per_page="3")
        self.image_url = f.photos.getSizes(photo_id=photos["photos"]["photo"][0]["id"])["sizes"]["size"][4]["source"]
        return self

    def extract_data(self, api_config):
        if self.image_url:
            return self
        credential_bing = (b"Basic " + base64.b64encode(api_config["BING_KEY"] + b":" + api_config["BING_KEY"])).decode(
            "latin1"
        )
        search = "%27{0}%27".format(urllib.parse.quote(self.word))
        top = 2
        offset = 0
        url = "https://api.datamarket.azure.com/Bing/Search/v1/Image?Query={0}&$format=json".format(search)
        request = urllib.request.Request(url)
        request.add_header("Authorization", credential_bing)
        response = urllib.request.urlopen(request)
        response_data = response.read().decode("utf8")
        json_result = json.loads(response_data)
        result_list = json_result["d"]["results"]
        self.image_url = result_list[0]["MediaUrl"]
        return self


class Noun(WordWithImage):
    pass


class Organization(WordType):
    def __init__(self, word, abstract="", logo_url=None):
        self.word = word
        self.abstract = abstract
        self.logo_url = logo_url


class Celebrity(WordType):
    def __init__(self, word, abstract="", image_url=None):
        self.word = word
        self.abstract = abstract
        self.image_url = image_url


class Musician(WordType):
    def __init__(self, word, abstract="", playlist_url=None, image_url=None):
        self.word = word
        self.abstract = abstract
        self.playlist_url = playlist_url
        self.image_url


class Actor(WordType):
    def __init__(self, word, abstract="", image_url=None, imdb_url=None):
        self.word = word
        self.abstract = abstract
        self.image_url = image_url
        self.imdb_url = imdb_url


class Event(WordType):
    def __init__(self, word, abstract="", time=None):
        self.word = word
        self.abstract = abstract
        self.time = time


class Location(WordType):
    def __init__(self, word, abstract="", map_url=None):
        self.word = word
        self.abstract = abstract
        self.map_url = map_url


class Verb(WordWithImage):
    pass


class Adjective(WordWithImage):
    pass


class Color(WordType):
    def __init__(self, word):
        self.word = word


class Link(WordType):
    def __init__(self, word):
        self.word = word


class Unknown(WordType):
    def __init__(self, word):
        self.word = word
