from pathlib import Path
from single_version import get_version

VERSION = get_version("pretext", Path(__file__).parent.parent)

CORE_COMMIT = "7b1825851e008cb7fc56f2099da354728f7e9edd"


def activate() -> None:
    raise RuntimeError(
        "As of version 1.0, the `pretext` PyPI package has been "
        + "transferred to PreTeXtBook.org. Install a <1.0 version to use the "
        + "pretext.activate() feature from the original `pretext` package."
    )
