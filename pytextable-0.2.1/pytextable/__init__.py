__license__ = "GPL3"
__version_info__ = (0, 2, 1)
__version__ = ".".join(str(num) for num in __version_info__)
__author__ = "Christian Karl"
__maintainer__ = __author__
__email__ = "karlch@protonmail.com"
__description__ = "Utilities to convert python data to latex tables."
__url__ = "https://github.com/karlch/pytextable"
from ._pytextable import DataT, HeaderT, MidruleCallbackT, RowT, tostring, write
