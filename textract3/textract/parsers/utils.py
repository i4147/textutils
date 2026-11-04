import subprocess
import tempfile
import os
import errno

import six
import chardet

from .. import exceptions


class BaseParser(object):
    def extract(self, filename, **kwargs):
        raise NotImplementedError("must be overwritten by child classes")

    def encode(self, text, encoding):
        return text.encode(encoding, "ignore")

    def process(self, filename, input_encoding, output_encoding="utf8", **kwargs):
        byte_string = self.extract(filename, **kwargs)
        unicode_string = self.decode(byte_string, input_encoding)
        return self.encode(unicode_string, output_encoding)

    def decode(self, text, input_encoding=None):
        if isinstance(text, six.text_type):
            return text

        if not text:
            return ""

        if input_encoding:
            return text.decode(input_encoding)

        result = chardet.detect(text)
        encoding = result["encoding"] if result["confidence"] > 0.80 else "utf8"
        return text.decode(encoding, errors="replace")


class ShellParser(BaseParser):
    def run(self, args):

        try:
            pipe = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise exceptions.ShellError(
                    " ".join(args),
                    127,
                    "",
                    "",
                )
            else:
                raise

        stdout, stderr = pipe.communicate()

        if pipe.returncode != 0:
            raise exceptions.ShellError(
                " ".join(args),
                pipe.returncode,
                stdout,
                stderr,
            )

        return stdout, stderr

    def temp_filename(self):
        handle, filename = tempfile.mkstemp()
        os.close(handle)
        return filename
