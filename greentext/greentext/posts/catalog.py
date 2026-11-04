from typing import List

from greentext.posts.threads import Thread

url = "https://a.4cdn.org/{board}/catalog.json"
pages = []


class Page(object):
    def __eq__(self, other):
        if other.__class__ is self.__class__:
            return (self.page, self.threads) == (other.page, other.threads)
        else:
            return NotImplemented

    def __hash__(self):
        return hash((self.page, self.threads))

    def __init__(self, page: dict):
        self.page = page.get("page")
        self.threads = [thread for thread in page.get("threads")]

    def __repr__(self):
        return "<Page({}, {} threads)>".format(self.page, len(self.threads))
