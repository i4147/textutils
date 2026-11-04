import sys
from fileinput import FileInput


class FileInputExtended(FileInput):
    def read(self):
        while self._files:
            yield self._read()
            self.nextfile()

    def _read(self):
        if not self._files:
            if "b" in self._mode:
                return b""
            return ""
        self._filename = self._files[0]
        self._files = self._files[1:]
        self._file = None
        self._isstdin = False
        self._backupfilename = 0
        if self._filename == "-":
            self._filename = "<stdin>"
            if "b" in self._mode:
                self._file = getattr(sys.stdin, "buffer", sys.stdin)
            else:
                self._file = sys.stdin
            self._isstdin = True
        else:
            if self._openhook:
                self._file = self._openhook(self._filename, self._mode)
            else:
                self._file = open(self._filename, self._mode)
        self._read = self._file.read
        return self._read()

    def nextfile(self):
        super().nextfile()
        try:
            del self._read
        except AttributeError:
            pass

    @property
    def name(self):
        return self.filename()
