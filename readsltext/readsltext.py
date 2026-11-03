from collections import OrderedDict

__projectname__ = "readsltext"
__version__ = "0.0.6a5"
__laststableversion__ = "0.0.4"
__author__ = "Xavier Faure (suizokukan / 94.23.197.37)"
__copyright__ = "Copyright 2018, suizokukan"
__license__ = "GPL-3.0"
__licensepypi__ = "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
__maintainer__ = "Xavier Faure (suizokukan)"
__email__ = "suizokukan@orange.fr"
__status__ = "Pre-Alpha"
__statuspypi__ = "Development Status :: 2 - Pre-Alpha"


def clientrypoint():
    print("project {0} (v. {1}); author : {2}".format(__projectname__, __version__, __author__))


class ReadSLText(object):
    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        self.close()

    def __init__(self, filename, sep_char="»", ordereddicts=True):
        self.sep_char = sep_char
        self._file = None
        self.ordereddicts = ordereddicts
        self.open(filename)

    def __iter__(self):
        return next(self)

    def __next__(self):
        go_on = True
        full_line = self.get_empty_full_line()
        while go_on:
            line = self._file.readline()
            if line == "":
                go_on = False
            elif line.strip().startswith("#"):
                pass
            elif line.strip() == "":
                pass
            else:
                if self.sep_char not in line:
                    if full_line[0] != "":
                        yield full_line
                    elif full_line[1]:
                        raise ValueError("ill-formed lines : don't known what to with " + str(full_line[1]))
                    full_line = self.get_empty_full_line()
                    yield [line.strip(), None]
                elif line.count(self.sep_char) == 3:
                    if full_line[0] != "":
                        yield full_line
                    elif full_line[1]:
                        raise ValueError("ill-formed lines : don't known what to with " + str(full_line[1]))
                    full_line = self.get_empty_full_line()
                    yield list(map(str.strip, line.split(self.sep_char * 3)))
                elif line.count(self.sep_char) == 4:
                    if full_line[0] != "":
                        yield full_line
                    elif full_line[1]:
                        raise ValueError("ill-formed lines : don't known what to with " + str(full_line[1]))
                    full_line = self.get_empty_full_line()
                    _full_line = list(map(str.strip, line.split(self.sep_char * 3)))
                    full_line[0] = _full_line[0]
                    subdict = list(map(str.strip, _full_line[1].split(self.sep_char)))
                    full_line[1].update({subdict[0]: subdict[1]})
                else:
                    subdict = list(map(str.strip, line.split(self.sep_char)))
                    full_line[1].update({subdict[0]: subdict[1]})

    def close(self):
        self._file.close()

    def get_empty_full_line(self):
        if self.ordereddicts:
            return ["", OrderedDict()]
        return ["", dict()]

    def next(self):
        return self.__next__()

    def open(self, filename):
        self._file = open(filename, mode="r")
