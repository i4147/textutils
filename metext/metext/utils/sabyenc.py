import binascii
import re

import chardet


def correct_unknown_encoding(str_or_bytes_in):
    if not isinstance(str_or_bytes_in, bytes):
        str_or_bytes_in = str_or_bytes_in.encode("utf-8", "surrogateescape")

    try:
        return str_or_bytes_in.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return str_or_bytes_in.decode("ISO-8859-1")
        except ValueError:
            return str_or_bytes_in.decode(chardet.detect(str_or_bytes_in)["encoding"])


def old_yenc(data_plain):
    data = []

    new_lines = data_plain.split(b"\r\n")
    for i in range(len(new_lines)):
        if new_lines[i][:2] == b"..":
            new_lines[i] = new_lines[i][1:]
    if new_lines[-1] == b".":
        new_lines = new_lines[1:-1]
    data.extend(new_lines)

    yenc, data = parse_yenc_data(data)
    ybegin, ypart, yend = yenc

    flat_yenc_data = b"".join(data)

    for i in (0, 9, 10, 13, 27, 32, 46, 61):
        j = b"=%c" % (i + 64)
        flat_yenc_data = flat_yenc_data.replace(j, b"%c" % i)

    from_bytes = b"".join([b"%c" % i for i in range(256)])
    to_bytes = b"".join([b"%c" % ((i + 256 - 42) % 256) for i in range(256)])
    translate_table = bytes.maketrans(from_bytes, to_bytes)
    decoded_data = flat_yenc_data.translate(translate_table)

    crc = binascii.crc32(decoded_data)
    partcrc = "%08X" % (crc & 2**32 - 1)

    crcname = "pcrc32" if ypart else "crc32"
    if crcname in yend:
        _partcrc = "0" * (8 - len(yend[crcname])) + yend[crcname].upper()
    else:
        _partcrc = None

    return decoded_data, ybegin["name"], _partcrc == partcrc


def parse_yenc_data(data):
    ybegin = None
    ypart = None
    yend = None

    for i in range(min(40, len(data))):
        try:
            if data[i].startswith(b"=ybegin "):
                splits = 3
                if data[i].find(b" part=") > 0:
                    splits += 1
                if data[i].find(b" total=") > 0:
                    splits += 1

                ybegin = get_yenc_data(data[i], splits)

                if data[i + 1].startswith(b"=ypart "):
                    ypart = get_yenc_data(data[i + 1])
                    data = data[i + 2 :]
                else:
                    data = data[i + 1 :]
                break
        except IndexError:
            break

    for i in range(-1, -11, -1):
        try:
            if data[i].startswith(b"=yend "):
                yend = get_yenc_data(data[i])
                data = data[:i]
                break
        except IndexError:
            break

    return ((ybegin, ypart, yend), data)


def get_yenc_data(line, splits=None):
    YSPLIT_RE = re.compile(b"([a-zA-Z0-9]+)=")

    fields = {}

    if splits:
        parts = YSPLIT_RE.split(line, splits)[1:]
    else:
        parts = YSPLIT_RE.split(line)[1:]

    if len(parts) % 2:
        return fields

    for i in range(0, len(parts), 2):
        key, value = parts[i], parts[i + 1]
        fields[correct_unknown_encoding(key)] = correct_unknown_encoding(value.strip())

    return fields


def yenc_subtract(char, subtract):
    char_diff = char - subtract
    if char_diff < 0:
        return 256 + char_diff
    return char_diff
