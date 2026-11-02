import enum
import os


class FileUse(enum.Enum):
    INPUT = (1,)
    GENERATED = (2,)
    OUTPUT = 3


class FileRef:
    def __init__(self, tag, ext, use, output_step=None):
        self.tag = tag
        self.output_step = None
        self.ext = ext
        self.use = use

    def __eq__(self, b):
        return self.tag == b.tag and self.ext == b.ext and self.use == b.use and self.output_step == b.output_step

    def to_str(self):
        if self.ext == None:
            return self.tag
        else:
            return self.tag + "." + self.ext

    def __hash__(self):
        return hash((self.tag, self.ext, self.use))


def to_fref(string, use, allow_absolute=False):
    if not allow_absolute and os.path.isabs(string):
        msg = "Use of absolute path {} where a relative path is required. You probably meant to use `externals`"
        raise ValueError(msg)
    tag, ext = os.path.splitext(string)
    if ext == "":
        ext = None
    else:
        ext = ext[1:]
    return FileRef(tag, ext, use)
