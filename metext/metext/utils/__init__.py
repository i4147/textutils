import itertools
import json
from collections import OrderedDict

import chardet


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def _create_keys_list(analyzed_data):
    keys = set()
    for item in analyzed_data:
        for f_name, f_value in item.get("formats", {}).items():
            for p_type, p_values in (f_value or {}).get("patterns", {}).items():
                keys.update(set(itertools.chain(*[list(v.keys()) for v in p_values])))
    return sorted(keys)


def convert_to_csv_format(analyzed_data: list, json_encoder=CustomJsonEncoder) -> list:
    out = []

    if not analyzed_data:
        return out

    keys = _create_keys_list(analyzed_data)
    excluded = {
        "name",
        "value_kind",
        "value",
    }

    for item in analyzed_data:
        source = item.get("name")
        for f_name, f_value in item.get("formats", {}).items():
            if not f_value:
                continue
            for p_type, p_values in f_value.get("patterns", {}).items():
                for v in p_values:
                    out.append(
                        OrderedDict(
                            [
                                ("source", str(source)),
                                ("format", str(f_name)),
                                ("pattern_type", str(p_type)),
                                (
                                    "pattern",
                                    json.dumps(v.get("value"), cls=json_encoder),
                                ),
                            ]
                            + [
                                (
                                    col_name,
                                    json.dumps(v.get(col_name), cls=json_encoder),
                                )
                                for col_name in keys
                                if col_name not in excluded
                            ]
                        )
                    )
    return out


def convert_to_table_format(analyzed_data: list) -> list:
    csv_out = convert_to_csv_format(analyzed_data)
    if not csv_out:
        return []
    return [list(csv_out[0].keys())] + [list(item.values()) for item in csv_out]


def str_from_bytes(bytes_):
    try:
        return bytes_.decode(
            "utf-8",
        )
    except UnicodeDecodeError:
        try:
            return bytes_.decode(
                "ISO-8859-1",
            )
        except ValueError:
            return bytes_.decode(
                chardet.detect(bytes_)["encoding"],
            )


def convert_to_bytes(obj):
    if isinstance(obj, bytes):
        return obj
    if isinstance(obj, str):
        return obj.encode()
    if isinstance(obj, int):
        return str(obj).encode()
    if isinstance(obj, dict):
        return str(obj).encode()
    if isinstance(obj, list):
        return str(obj).encode()
    if isinstance(obj, bool):
        return str(obj).encode()
    if isinstance(obj, bytearray):
        return bytes(obj)

    raise NotImplementedError
