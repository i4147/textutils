from datetime import datetime

from greentext.media import Media
from greentext.users import User


class Post(object):
    def __eq__(self, other):
        if other.__class__ is self.__class__:
            return () == ()
        else:
            return NotImplemented

    def __hash__(self):
        return hash(())

    def __init__(self, board, response):
        self.archive_time = (
            datetime.fromtimestamp(response.get("archived_on")) if response.get("archived_on") is not None else None
        )
        self.board = board
        self.comment = response.get("com")
        self.has_spoiler = response.get("spoiler")
        self.is_archived = response.get("archived")
        self.is_stickied = response.get("sticky")
        self.media = Media(self, response) if response.get("filename") is not None else None
        self.number = response.get("no")
        self.reply_to = response.get("resto")
        self.time = datetime.fromtimestamp(response.get("time")) if response.get("time") is not None else None
        self.title = response.get("sub")
        self.user = User(response)

    def __repr__(self):
        return "<Post(number={})>".format(self.number)

    def serialize(self):
        return {
            "board": self.board,
            "comment": self.comment,
            "number": self.number,
            "time": self.time.second,
            "title": self.title,
            "user": self.user.serialize(),
        }
