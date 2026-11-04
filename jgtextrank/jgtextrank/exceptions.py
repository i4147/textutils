# -*- coding: utf-8 -*-

MISSING_CORPUS_MESSAGE = """
Looks like you are missing some required data for this feature.

To download the necessary data, use the NLTK downloader to download the missing data: http://nltk.org/data.html
"""


class TextRankError(Exception):
    pass


class MissingCorpusError(TextRankError):
    def __init__(self, message=MISSING_CORPUS_MESSAGE, *args, **kwargs):
        super(MissingCorpusError, self).__init__(message, *args, **kwargs)
