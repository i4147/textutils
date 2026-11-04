try:
    from hashlib import blake2b
except ImportError:
    from pyblake2 import blake2b
from typing import Optional

from base58 import b58decode


def ss58_decode(address: str, valid_ss58_format: Optional[int] = None) -> str:

    if address.startswith("0x"):
        return address

    checksum_prefix = b"SS58PRE"

    address_decoded = b58decode(address)

    if address_decoded[0] & 0b01000000:
        ss58_format_length = 2
        ss58_format = (
            ((address_decoded[0] & 0b00111111) << 2)
            | (address_decoded[1] >> 6)
            | ((address_decoded[1] & 0b00111111) << 8)
        )
    else:
        ss58_format_length = 1
        ss58_format = address_decoded[0]

    if ss58_format in [46, 47]:
        raise ValueError("{} is a reserved SS58 format".format(ss58_format))

    if valid_ss58_format is not None and ss58_format != valid_ss58_format:
        raise ValueError("Invalid SS58 format")

    if len(address_decoded) in [3, 4, 6, 10]:
        checksum_length = 1
    elif len(address_decoded) in [
        5,
        7,
        11,
        34 + ss58_format_length,
        35 + ss58_format_length,
    ]:
        checksum_length = 2
    elif len(address_decoded) in [8, 12]:
        checksum_length = 3
    elif len(address_decoded) in [9, 13]:
        checksum_length = 4
    elif len(address_decoded) in [14]:
        checksum_length = 5
    elif len(address_decoded) in [15]:
        checksum_length = 6
    elif len(address_decoded) in [16]:
        checksum_length = 7
    elif len(address_decoded) in [17]:
        checksum_length = 8
    else:
        raise ValueError("Invalid address length")

    checksum = blake2b(checksum_prefix + address_decoded[0:-checksum_length]).digest()

    if checksum[0:checksum_length] != address_decoded[-checksum_length:]:
        raise ValueError("Invalid checksum")

    return address_decoded[ss58_format_length : len(address_decoded) - checksum_length].hex()
