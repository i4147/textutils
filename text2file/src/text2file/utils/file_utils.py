import hashlib
import mimetypes
import os
import re
import shutil
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lstrip(".").lower()


def get_mime_type(file_path: Union[str, Path]) -> Tuple[Optional[str], Optional[str]]:
    return mimetypes.guess_type(str(file_path))


def is_binary_file(file_path: Union[str, Path], chunk_size: int = 1024) -> bool:
    file_path = Path(file_path)

    binary_extensions = {
        *"jpg jpeg png gif bmp tiff webp ico psd svg".split(),
        *"zip tar gz bz2 7z rar xz z lz lzma lzo".split(),
        *"pdf doc docx xls xlsx ppt pptx odt ods odp".split(),
        *"mp3 wav ogg flac aac wma m4a mp4 avi mkv mov wmv flv webm m4v 3gp".split(),
        "mpg",
        "mpeg",
        "m2ts",
        "mts",
        "exe",
        "dll",
        "so",
        "dylib",
        "class",
        "jar",
        "war",
        "ear",
        "apk",
        "app",
        "db",
        "sqlite",
        "sqlite3",
        "mdb",
        "accdb",
        "frm",
        "myd",
        "myi",
        "ibd",
        "dat",
        "bin",
        "iso",
        "dmg",
        "img",
        "toast",
        "vcd",
        "msi",
        "msm",
        "msp",
    }

    ext = get_file_extension(file_path)
    if ext in binary_extensions:
        return True

    try:
        with open(file_path, "rb") as f:
            chunk = f.read(chunk_size)
            if b"\x00" in chunk:
                return True

            try:
                chunk.decode("utf-8")
            except UnicodeDecodeError:
                return True

    except (IOError, OSError):
        pass

    return False


def get_file_hash(
    file_path: Union[str, Path],
    algorithm: str = "sha256",
    chunk_size: int = 65536,
) -> str:
    file_path = Path(file_path)
    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def create_temp_file(
    suffix: str = None,
    prefix: str = None,
    dir: Union[str, Path] = None,
    text: bool = False,
) -> Path:
    if dir is not None:
        os.makedirs(dir, exist_ok=True)

    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir, text=text)
    os.close(fd)
    return Path(path)


def create_temp_dir(prefix: str = None, dir: Union[str, Path] = None) -> str:
    return tempfile.mkdtemp(prefix=prefix, dir=dir)


def safe_remove(path: Union[str, Path]) -> bool:
    try:
        path = Path(path)
        if path.is_file() or path.is_symlink():
            os.unlink(path)
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except (OSError, shutil.Error):
        return False


def ensure_directory(directory: Union[str, Path], mode: int = 0o755) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=mode)
    return directory


def copy_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    overwrite: bool = False,
) -> bool:
    src = Path(src)
    dst = Path(dst)

    if not src.is_file():
        return False

    if dst.exists() and not overwrite:
        return False

    try:
        shutil.copy2(src, dst)
        return True
    except (IOError, OSError, shutil.Error):
        return False


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    file_path = Path(file_path)

    if not file_path.exists():
        return {"exists": False, "path": str(file_path)}

    stat = file_path.stat()
    mime_type, encoding = get_mime_type(file_path)

    return {
        "exists": True,
        "path": str(file_path.absolute()),
        "name": file_path.name,
        "stem": file_path.stem,
        "suffix": file_path.suffix,
        "suffixes": file_path.suffixes,
        "parent": str(file_path.parent),
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
        "is_symlink": file_path.is_symlink(),
        "size": stat.st_size,
        "size_human": _format_size(stat.st_size),
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "accessed": stat.st_atime,
        "mode": oct(stat.st_mode)[-3:],
        "mime_type": mime_type,
        "encoding": encoding,
        "is_binary": is_binary_file(file_path) if file_path.is_file() else None,
    }


def _format_size(size: int, decimals: int = 2) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            break
        if unit != "TB":
            size /= 1024.0
    return f"{size:.{decimals}f} {unit}"


def find_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = True,
    case_sensitive: bool = False,
) -> List[Path]:
    directory = Path(directory)
    if not directory.is_dir():
        return []

    if case_sensitive:
        if recursive:
            return list(directory.rglob(pattern))
        return list(directory.glob(pattern))
    else:
        pattern = pattern.lower()
        matches = []

        def _match(p: Path) -> bool:
            return p.name.lower().endswith(pattern.lstrip("*"))

        if recursive:
            for p in directory.rglob("*"):
                if p.is_file() and _match(p):
                    matches.append(p)
        else:
            for p in directory.glob("*"):
                if p.is_file() and _match(p):
                    matches.append(p)

        return matches


def sanitize_filename(filename: str, replace_with: str = "_") -> str:

    normalized = unicodedata.normalize("NFKD", str(filename))
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")

    no_special = re.sub(r"[^\w\s-]", replace_with, ascii_str)
    no_whitespace = re.sub(r"[\s]+", replace_with, no_special)
    stripped = no_whitespace.strip(replace_with)

    if not stripped:
        return f"unnamed{replace_with}file"

    max_len = 255
    if len(stripped) > max_len:
        name, ext = os.path.splitext(stripped)
        ext = ext[: max(0, max_len - len(name) - 1)]
        stripped = name[: max(0, max_len - len(ext) - 1)] + ext

    return stripped
