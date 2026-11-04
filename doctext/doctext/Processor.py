# -*- coding: utf-8 -*-

from pathlib import Path
from doctext.Capabilities import Capabilities
from doctext.textextract import extract_text
import logging

# logging.basicConfig(level=logging.DEBUG)
# logging.debug('This will get logged')

print(f"Logging level: {logging.getLogger().getEffectiveLevel()}")


class Processor:
    def __init__(self, openai_api_key=None, tesseract_lang="deu"):
        self.openai_api_key = openai_api_key
        self.tesseract_lang = tesseract_lang
        self.capabilities = Capabilities(self.openai_api_key is not None)

    def run(self, file_path: str | Path) -> str:
        return extract_text(str(file_path), self.openai_api_key, self.tesseract_lang, self.capabilities)
