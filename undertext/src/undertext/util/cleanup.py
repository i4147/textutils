# -*- coding=utf-8 -*-

import html.parser


__all__ = ["html_cleanup"]


class HTMLCleaner(html.parser.HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pieces = []

    def handle_data(self, data: str):
        self.pieces.append(data)

    @property
    def text(self):
        return "".join(self.pieces)


def html_cleanup(text: str) -> str:
    cleaner = HTMLCleaner()
    cleaner.feed(text)
    return cleaner.text


if __name__ == "__main__":
    print(html_cleanup("Like internet experiences that are rich <c.highlight>and</c> entertaining"))
