import bz2
import concurrent.futures as cf
import gzip
import io
import lzma
import os
import tarfile
import zipfile
from io import BytesIO, StringIO
from typing import Any, Callable, List, Optional, Tuple, Union

import brotli
from filetype import guess_mime

from metext import plugin_base
from metext.plugin_base import BaseDecoder, BaseExtractor, Decodable
from metext.plugins import load_plugin_modules
from metext.utils import (
    convert_to_bytes,
    str_from_bytes,
    convert_to_csv_format,
    convert_to_table_format,
)
from metext.utils.fileinput import FileInputExtended

register_plugin_modules = load_plugin_modules


def list_decoders(active_only: bool = True) -> dict:
    if active_only:
        return {plug.PLUGIN_NAME: plug for plug in plugin_base.BaseDecoder.get_active_plugins()}
    return {plug.PLUGIN_NAME: plug for plug in plugin_base.BaseDecoder.get_plugins()}


def list_extractors(active_only: bool = True) -> dict:
    if active_only:
        return {plug.PLUGIN_NAME: plug for plug in plugin_base.BaseExtractor.get_active_plugins()}
    return {plug.PLUGIN_NAME: plug for plug in plugin_base.BaseExtractor.get_plugins()}


def list_printers(active_only: bool = True) -> dict:
    if active_only:
        return {plug.PLUGIN_NAME: plug for plug in plugin_base.BasePrinter.get_active_plugins()}
    return {plug.PLUGIN_NAME: plug for plug in plugin_base.BasePrinter.get_plugins()}


def get_decoder(name) -> Optional[Callable]:
    try:
        return list_decoders().get(name).run
    except:
        return None


def get_extractor(name) -> Optional[Callable]:
    try:
        return list_extractors().get(name).run
    except:
        return None


def get_printer(name) -> Optional[Callable]:
    try:
        return list_printers().get(name).run
    except:
        return None


def __is_supported_decoder(decoder: str):
    return decoder in list_decoders().keys()


def __is_supported_extractor(extractor: str):
    return extractor in list_extractors().keys()


def __is_supported_printer(printer: str):
    return printer in list_printers().keys()


def decode(data: Decodable, decoder: str, **kwargs) -> Optional[Any]:
    if not decoder:
        return data

    if not __is_supported_decoder(decoder):
        raise ValueError("Invalid decoder. Supported values: {}".format(list(list_decoders_names())))

    return get_decoder(decoder)(data, **kwargs)


def list_decoders_names(active_only: bool = True) -> list:
    return list(list_decoders(active_only=active_only).keys())


def list_extractors_names(active_only: bool = True) -> list:
    return list(list_extractors(active_only=active_only).keys())


def list_printers_names(active_only: bool = True) -> list:
    return list(list_printers(active_only=active_only).keys())


def extract_patterns(data: str, extractor: str, **kwargs) -> List[Any]:
    if not __is_supported_extractor(extractor):
        raise ValueError("Invalid extractor name. Supported values: {}".format(list_extractors_names(active_only=True)))

    if not isinstance(data, str):
        data = str_from_bytes(data)

    return list(get_extractor(extractor)(data, **kwargs))


def analyse(
    _input: Union[FileInputExtended, BytesIO, StringIO, str, bytes],
    decoders: Union[List[Tuple[str, dict]], List[str], str] = None,
    extractors: Union[List[Tuple[str, dict]], List[str], str] = None,
    **kwargs,
) -> List[dict]:

    def __read(_value):
        if isinstance(_value, str):
            _value = StringIO(_value)
        elif isinstance(_value, (bytes, bytearray)):
            _value = BytesIO(_value)
        if isinstance(_value, list):
            _value = FileInputExtended(_value, mode="rb")
        if isinstance(_value, FileInputExtended):
            return _value.read()
        return (_value.read(),)

    def __add_patterns_to_out(_source: str, _format: str, _patterns: dict, _out: dict):
        item = _out.setdefault(_source, {})
        item.setdefault("name", _source)
        item_formats = item.setdefault("formats", {})
        if not _patterns and _format not in item_formats:
            item_formats[_format] = None
            return
        item_formats[_format] = item_formats.get(_format) or {}
        for k, v in _patterns.items():
            item_formats[_format].setdefault("patterns", {}).setdefault(k, []).extend(v)

    if not decoders or decoders in ["auto", "all"]:
        decoders = [(dec_name, {}) for dec_name in list_decoders().keys()]
    if isinstance(decoders, str):
        decoders = [(decoders, {})]
    decoders = [d if isinstance(d, tuple) else (d, {}) for d in decoders]

    if not extractors or extractors in ["auto", "all"]:
        extractors = [(ex_name, {}) for ex_name in list_extractors().keys()]
    if isinstance(extractors, str):
        extractors = [(extractors, {})]
    extractors = [e if isinstance(e, tuple) else (e, {}) for e in extractors]

    exclusive_decoders_dict = __create_decoders_exclusivity()
    out = {}

    max_workers = kwargs.get("max_workers", None)
    if max_workers is None:
        max_workers = max([min([len(extractors), os.cpu_count() - 1]), 1])
    with cf.ProcessPoolExecutor(max_workers=max_workers) as e:
        success_decode_extract = {}
        for data_read in __read(_input):
            try:
                source_name = _input.name
            except:
                source_name = "<data>"
            dl, dec_name_pre = __decompress_to_data_list(data_read)
            for data in dl:
                for dec in decoders:
                    dec_name, dec_kwargs = dec
                    skip_decoder = bool(
                        exclusive_decoders_dict.get(dec_name, set()) & success_decode_extract.get(source_name, set())
                    )
                    if skip_decoder:
                        continue

                    data_list, dec_name_post = __decompress_to_data_list(decode(data, dec_name, **dec_kwargs))
                    for decoded_data in data_list:
                        if not decoded_data:
                            continue
                        patterns = {}
                        future_extracted = {
                            e.submit(
                                __extract_single,
                                str_from_bytes(decoded_data),
                                extractor,
                            ): extractor[0]
                            for extractor in extractors
                        }
                        for future in cf.as_completed(future_extracted):
                            pattern_type = future_extracted[future]
                            try:
                                result = future.result()
                                if result:
                                    patterns[pattern_type] = result
                                    success_decode_extract.setdefault(source_name, set()).add(dec_name)
                            except:
                                pass
                        dec_name_final = "+".join(n for n in (dec_name_pre, dec_name, dec_name_post) if bool(n))
                        __add_patterns_to_out(source_name, dec_name_final, patterns, out)
            if source_name not in out:
                out[source_name] = {
                    "name": source_name,
                    "message": "Couldn't decode data nor find any patterns.",
                }

    return list(out.values())


def __extract_single(_data, _extractor):
    ex_name, ex_kwargs = _extractor
    return extract_patterns(_data, ex_name, **ex_kwargs)


def __create_decoders_exclusivity():
    exclusive_decoders = (
        ("hex", "hexdump"),
        ("base64", "base64url"),
        ("base32", "base32hex", "base32crockford"),
        ("base85", "z85", "ascii85"),
        ("base58btc", "base58ripple"),
    )
    exclusive_decoders_dict = {
        d: {
            "hex",
            "hexdump",
            "base91",
            "base58btc",
            "base58ripple",
            "z85",
            "ascii85",
            "base85",
            "binhex",
            "yenc",
            "uu",
        }
        for d in list_decoders_names()
    }
    for edp in exclusive_decoders:
        for ed in edp:
            exclusive_decoders_dict.setdefault(ed, set()).update(edp)
    for i in ("raw", "percent", "quopri"):
        exclusive_decoders_dict[i].update({
            i,
            "base32",
            "base32hex",
        })
    return exclusive_decoders_dict


def __decompress_to_data_list(data):
    if not data:
        return [], ""
    data = convert_to_bytes(data)
    mime = guess_mime(data)
    try:
        if mime == "application/x-tar":
            with tarfile.open(fileobj=io.BytesIO(data)) as tf:
                return [tf.extractfile(f).read() for f in tf.getmembers()], "tar"
        if mime == "application/gzip":
            with tarfile.open(fileobj=io.BytesIO(data)) as tf:
                return [tf.extractfile(f).read() for f in tf.getmembers()], "gzip+tar"
        if mime == "application/x-xz":
            with tarfile.open(fileobj=io.BytesIO(data)) as tf:
                return [tf.extractfile(f).read() for f in tf.getmembers()], "xz+tar"
        if mime == "application/x-bzip2":
            with tarfile.open(fileobj=io.BytesIO(data)) as tf:
                return [tf.extractfile(f).read() for f in tf.getmembers()], "bzip2+tar"
    except:
        pass

    try:
        if mime == "application/gzip":
            return [gzip.decompress(data)], "gzip"
        if mime in ("application/zip", "application/epub+zip"):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                return [zf.read(f) for f in zf.infolist()], "zip"
        if mime == "application/x-brotli":
            return [brotli.decompress(data)], "brotli"
        if mime == "application/x-bzip2":
            return [bz2.decompress(data)], "bzip2"
        if mime == "application/x-xz":
            return [lzma.decompress(data)], "xz"
        if mime in ("application/x-lzip", "application/x-lzma"):
            return [lzma.decompress(data)], "lzma"
    except:
        pass

    try:
        return [brotli.decompress(data)], "brotli"
    except:
        pass

    return [data], ""


def print_analysis_output(data, filename="-", printer="json", **kwargs):
    assert __is_supported_printer(printer) is True

    to_print = data
    if printer == "csv":
        to_print = convert_to_csv_format(data)
    if printer == "text":
        to_print = convert_to_table_format(data)
    get_printer(printer)(to_print, filename=filename, **kwargs)
