import speech_recognition as sr
import os

from ..exceptions import UnknownMethod, ShellError
from .utils import ShellParser


class Parser(ShellParser):
    def extract(self, filename, method="", **kwargs):
        speech = ""

        base, ext = os.path.splitext(filename)
        if ext != ".wav":
            temp_filename = self.convert_to_wav(filename)
            try:
                speech = self.extract(temp_filename, method, **kwargs)
            finally:
                os.remove(temp_filename)
        else:
            r = sr.Recognizer()

            with sr.WavFile(filename) as source:
                audio = r.record(source)

            try:
                if method == "google" or method == "":
                    speech = r.recognize_google(audio)
                elif method == "sphinx":
                    speech = r.recognize_sphinx(audio)
                else:
                    raise UnknownMethod(method)
            except LookupError:
                speech = ""
            except sr.UnknownValueError:
                speech = ""

            speech += "\n"

        return speech

    def convert_to_wav(self, filename):
        temp_filename = "{0}.wav".format(self.temp_filename())
        self.run(["sox", "-G", "-c", "1", filename, temp_filename])
        return temp_filename
