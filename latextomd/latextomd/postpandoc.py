import re
from latextomd import config


class Postpandoc(object):
    def __init__(self, markdown):
        self.content = markdown

    def process(self):
        self._replace()

        return self.content

    def _replace(self):
        for item in config.postpandoc:
            p = re.compile(item[0])
            self.content = p.sub(item[1], self.content)
