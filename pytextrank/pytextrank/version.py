# -*- coding: utf-8 -*-


from os.path import dirname, abspath
import pathlib
import typing

from git import Repo


REPO_HASH: str = "xxxxxxxxx"
REPO_TAGS: str = "refs/tags/v1.0.0"

try:
    repo_path: pathlib.Path = pathlib.Path(dirname(abspath(__file__)))
    repo: Repo = Repo(repo_path.parents[0])

    REPO_HASH = str(repo.head.commit)
    REPO_TAGS = repo.tags
except Exception as ex:
    print(ex)


try:
    v_seq: typing.List[str] = str(REPO_TAGS[-1]).replace("v", "").split(".")[:3]

    __version__ = ".".join(v_seq)

    __version_major__ = int(v_seq[0])
    __version_minor__ = int(v_seq[1])
    __version_patch__ = int(v_seq[2])
except IndexError:
    __version__ = "0.0+test"

    __version_major__ = 0
    __version_minor__ = 0
    __version_patch__ = 0


def get_repo_version() -> typing.Tuple[str, str]:
    return __version__, REPO_HASH
