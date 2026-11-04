# -*- coding=utf-8 -*-

__author__ = "PlayerG9"
__copyright__ = "Copyright 2024, utility-libraries"
__credits__ = ["PlayerG9"]
__license__ = "MIT"
__maintainer__ = "PlayerG9"
__email__ = None
__status__ = "Prototype"
__description__ = "library to load, edit and save different formats of subtitles"
__version_info__ = (0, 4, 1)
__version__ = ".".join(str(_) for _ in __version_info__)

from .exceptions import *
from .structures import *
from . import readers, writers
from .readers import load, loads
from .writers import dump, dumps
from .extra import clean_captions
