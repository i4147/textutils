# -*- coding: utf-8 -*-

from __future__ import absolute_import
from functools import wraps
from jgtextrank.exceptions import MissingCorpusError


class cached_property(object):
    def __init__(self, func):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def requires_nltk_corpus(func):

    @wraps(func)
    def decorated(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LookupError as err:
            print(err)
            raise MissingCorpusError()

    return decorated
