from binascii import crc32
from hashlib import sha256
from typing import Optional, Union

import base58
import cashaddress
import cbor
import sha3

from metext.plugin_base import BaseValidator
from metext.plugins.decoders.base58 import CHARSETS, Base58Decoder
from metext.plugins.decoders.bech32 import Bech32Decoder
from metext.plugins.decoders.segwit import SegwitDecoder
from metext.utils.regex import RE_ETH
from metext.utils.ss58 import ss58_decode


def is_valid_base58_address(
    address: Union[bytes, str],
    prefixes: Optional[list] = None,
    charset=CHARSETS["bitcoin"],
    specs: Optional[list] = None,
) -> bool:
    if prefixes is None and specs is None:
        specs = [b"\x00", b"\x05"]

    try:
        if not isinstance(address, str):
            address = address.decode("ascii")

        if prefixes and address[0] not in prefixes:
            return False
        bc_bytes = Base58Decoder.run(address, charset=charset)
        if specs and bc_bytes[0] not in (ord(s) for s in specs):
            return False
        return bc_bytes[-4:] == sha256(sha256(bc_bytes[:-4]).digest()).digest()[:4]
    except:
        return False


def is_valid_segwit_address(address, hrps=None) -> bool:
    if hrps is None:
        hrps = ["bc"]

    try:
        return any(SegwitDecoder.run(address, hrp=hrp) != (None, None) for hrp in hrps)
    except:
        return False


class BitcoinValidator(BaseValidator):
    PLUGIN_NAME = "btc"

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        return is_valid_base58_address(_input, prefixes=["1", "3"]) or is_valid_segwit_address(_input, hrps=["bc"])


class BitcoinWifValidator(BaseValidator):
    PLUGIN_NAME = "btc-wif"

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        try:
            base58.b58decode_check(_input)
        except:
            return False

        return True


class BitcoinPrivKeyValidator(BaseValidator):
    PLUGIN_NAME = "btc-privkey"

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        if isinstance(_input, str):
            try:
                _input = _input.encode("ascii").lower()
            except:
                return False

        if len(_input) != 64 or _input > b"fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140":
            return False

        try:
            wif = base58.b58encode_check(b"80" + _input)
        except:
            try:
                wif = base58.b58encode_check(b"ef" + _input)
            except:
                return False

        return BitcoinWifValidator.run(wif)


class BitcoinCashValidator(BaseValidator):
    PLUGIN_NAME = "bch"
    PLUGIN_ACTIVE = False

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        if not isinstance(_input, str):
            try:
                _input = _input.decode("ascii")
            except:
                return False

        _input = "bitcoincash:" + _input if _input[0].lower() in ["q", "p"] else _input
        return cashaddress.convert.is_valid(_input)


class EthereumValidator(BaseValidator):
    PLUGIN_NAME = "eth"

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        try:
            if not isinstance(_input, str):
                _input = _input.decode("ascii")

            if not RE_ETH.match(_input):
                return False

            _input = _input[2:]
            if _input.lower() == _input or _input.upper() == _input:
                return True

            _hash = sha3.keccak_256(_input.lower().encode("ascii")).hexdigest()
            return not any(
                (int(_hash[i], 16) > 7 and _input[i].upper() != _input[i])
                or (int(_hash[i], 16) <= 7 and _input[i].lower() != _input[i])
                for i in range(len(_input))
            )
        except Exception:
            return False


class LitecoinValidator(BaseValidator):
    PLUGIN_NAME = "ltc"

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        return is_valid_base58_address(_input, prefixes=["L", "M", "3"]) or is_valid_segwit_address(
            _input, hrps=["ltc"]
        )


class RippleValidator(BaseValidator):
    PLUGIN_NAME = "xrp"

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        return is_valid_base58_address(_input, prefixes=["r"], charset=CHARSETS["ripple"])


class TetherValidator(BaseValidator):
    PLUGIN_NAME = "usdt"

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        return is_valid_base58_address(
            _input, charset=CHARSETS["bitcoin"], specs=[b"\x00", b"\x05"]
        ) or EthereumValidator.run(_input)


class ChainlinkValidator(BaseValidator):
    PLUGIN_NAME = "chainlink"

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        return EthereumValidator.run(_input)


class CardanoValidator(BaseValidator):
    PLUGIN_NAME = "ada"

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        return cls.is_valid_address_byron(_input) or cls.is_valid_address_shelley(_input)

    @classmethod
    def is_valid_address_shelley(cls, address):
        hrp, decoded = Bech32Decoder.run(address, max_length=110)
        if decoded is None:
            return False

        return hrp in ["addr", "stake"]

    @classmethod
    def is_valid_address_byron(cls, address):
        try:
            decoded = cls._get_decoded(address)
            if not decoded or len(decoded) != 2:
                return False
            tag = decoded[0]
            expected_crc = decoded[1]
            return expected_crc == crc32(tag.value)
        except:
            return False

    @classmethod
    def _get_decoded(cls, address):
        decoded = Base58Decoder.run(address)
        if not decoded:
            return None
        decoded = decoded.lstrip(b"\x00")
        try:
            return cbor.loads(decoded)
        except:
            return None


class PolkadotValidator(BaseValidator):
    PLUGIN_NAME = "dot"

    @classmethod
    def run(cls, _input: Union[bytes, str], **kwargs) -> bool:
        try:
            if not isinstance(_input, str):
                _input = _input.decode("ascii")

            if _input.startswith("0x"):
                return False

            ss58_decode(_input)
        except:
            return False

        return True
