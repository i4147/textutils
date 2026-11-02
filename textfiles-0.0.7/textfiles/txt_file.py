from .text_file_parent import TextFile
from .exceptions import *
import os


class TxtFile(TextFile):
    def __init__(self, file_path):
        super().__init__(file_path)
        self.lines = self._read_lines()

    @staticmethod
    def _specific_content(fd):
        return fd.read()

    def _read_lines(self):
        with open(self.file_path) as fh:
            lines = fh.readlines()
        return lines

    def __add__(self, other) -> bool:
        if not isinstance(other, TxtFile):
            raise ValueError("both files must be .txt")
        self.lock.acquire()
        new_name = os.path.join(self.root, self.file_name + "_" + other.file_name + "." + self._ext)
        if os.path.exists(new_name):
            raise PathAlreadyExistsError(new_name)
        with open(new_name, "x") as fh:
            fh.write(self._content + other._content)
        self.lock.release()
        return True

    def __len__(self) -> int:
        return len(self.words)

    def __contains__(self, item: str | int) -> bool:
        if item in self._content:
            return True
        else:
            return False

    def __iter__(self):
        return iter(self.words)

    def __str__(self):
        return (
            f"{self.file_name}\n"
            f"contains {len(self.lines)} lines\n"
            f"file creation time: {self.creation_time}\n"
            f"file last modified: {self.last_modified}"
        )

    @property
    def words(self) -> list:
        to_remove = []
        list_of_words = self._content.split()
        for i in range(len(list_of_words)):
            if list_of_words[i][-1] == "-":
                list_of_words[i] = list_of_words[i][0:-2] + list_of_words[i + 1]
                to_remove.append(list_of_words[i + 1])
        for word in to_remove:
            list_of_words.remove(word)
        return list_of_words

    def search(self, val):
        if val not in self:
            return None
        findings = []
        for index, line in enumerate(self.lines):
            if val in line:
                findings.append((index, line))
        return findings

    def add_line(self, line, line_num=None):
        if line_num is None:
            line_num = len(self.lines)
            self.lock.acquire()
            with open(self._file_path, "a") as fh:
                fh.write(f"\n{line}\n")
            self.lock.release()
        else:
            self.lock.acquire()
            new_text = self.lines[:line_num] + line + self.lines[line_num:]
            with open(self.file_path, "w") as fh:
                fh.write(new_text)
            self.lock.release()

    def count(self, val) -> int:
        return self.content.count(val)

    def _ext(self):
        return "txt"
