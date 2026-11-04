import struct

Z85CHARS = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-:+=^!/*?&<>()[]{}@%$#"
Z85MAP = dict([(c, idx) for idx, c in enumerate(Z85CHARS)])

_85s = [85**i for i in range(5)][::-1]


def encode(rawbytes):
    if len(rawbytes) % 4:
        raise ValueError("length must be multiple of 4, not %i" % len(rawbytes))

    nvalues = len(rawbytes) / 4

    values = struct.unpack(">%dI" % nvalues, rawbytes)
    encoded = []
    for v in values:
        for offset in _85s:
            encoded.append(Z85CHARS[(v // offset) % 85])

    return bytes(encoded)


def decode(z85bytes):
    if isinstance(z85bytes, str):
        try:
            z85bytes = z85bytes.encode("ascii")
        except UnicodeEncodeError:
            raise ValueError("string argument should contain only ASCII characters")

    if len(z85bytes) % 5:
        raise ValueError("Z85 length must be multiple of 5, not %i" % len(z85bytes))

    nvalues = len(z85bytes) / 5
    values = []
    for i in range(0, len(z85bytes), 5):
        value = sum(Z85MAP[z85bytes[i + j]] * offset for j, offset in enumerate(_85s))
        values.append(value)
    return struct.pack(">%dI" % nvalues, *values)
