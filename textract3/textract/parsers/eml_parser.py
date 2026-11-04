from email.parser import Parser as EmailParser

from .utils import BaseParser


class Parser(BaseParser):
    def extract(self, filename, **kwargs):

        with open(filename) as stream:
            parser = EmailParser()
            message = parser.parse(stream)

        text_content = []
        for part in message.walk():
            if part.get_content_type().startswith("text/plain"):
                text_content.append(part.get_payload())
        return "\n\n".join(text_content)
