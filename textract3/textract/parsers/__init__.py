import os
import importlib
import glob
import re

from .. import exceptions

EXTENSION_SYNONYMS = {
    ".jpeg": ".jpg",
    ".tff": ".tiff",
    ".tif": ".tiff",
    ".htm": ".html",
    "": ".txt",
    ".log": ".txt",
    ".tab": ".tsv",
}

DEFAULT_OUTPUT_ENCODING = "utf_8"
DEFAULT_ENCODING = "utf_8"

_FILENAME_SUFFIX = "_parser"


def process(filename, input_encoding=None, output_encoding=DEFAULT_OUTPUT_ENCODING, extension=None, **kwargs):

    if not os.path.exists(filename):
        raise exceptions.MissingFileError(filename)

    if extension:
        ext = extension
        if not ext.startswith("."):
            ext = "." + ext
        ext = ext.lower()
    else:
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

    ext = EXTENSION_SYNONYMS.get(ext, ext)

    rel_module = ext + _FILENAME_SUFFIX

    try:
        filetype_module = importlib.import_module(rel_module, "textract.parsers")
    except ImportError:
        raise exceptions.ExtensionNotSupported(ext)

    parser = filetype_module.Parser()
    return parser.process(filename, input_encoding, output_encoding, **kwargs)


def _get_available_extensions():
    extensions = []

    parsers_dir = os.path.join(os.path.dirname(__file__))
    glob_filename = os.path.join(parsers_dir, "*" + _FILENAME_SUFFIX + ".py")
    glob_filename = glob_filename.replace("//", "////")
    ext_re = re.compile(glob_filename.replace("*", r"(?P<ext>\w+)"))
    for filename in glob.glob(glob_filename):
        ext_match = ext_re.match(filename)
        ext = ext_match.groups()[0]
        extensions.append(ext)
        extensions.append("." + ext)

    for ext in EXTENSION_SYNONYMS.keys():
        if ext:
            extensions.append(ext)
            extensions.append(ext.replace(".", "", 1))
    extensions.sort()
    return extensions
