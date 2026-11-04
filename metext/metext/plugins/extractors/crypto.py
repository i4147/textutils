from typing import Iterable

from metext.plugins.extractors import _extract_with_regex

try:
    from btclib import slip132

    has_btclib = True
except ImportError:
    has_btclib = False

from metext.plugin_base import BaseExtractor
from metext.plugins.validators.crypto import (
    BitcoinCashValidator,
    BitcoinPrivKeyValidator,
    BitcoinValidator,
    BitcoinWifValidator,
    CardanoValidator,
    ChainlinkValidator,
    EthereumValidator,
    LitecoinValidator,
    PolkadotValidator,
    RippleValidator,
    TetherValidator,
)
from metext.utils.regex import (
    RE_ADA,
    RE_BCH,
    RE_BCH_WITH_LEGACY,
    RE_BIP32_XKEY,
    RE_BTC,
    RE_BTC_PRIVKEY,
    RE_BTC_WIF,
    RE_DOT,
    RE_ETH,
    RE_LINK,
    RE_LTC,
    RE_USDT,
    RE_XRP,
)


class BitcoinAddress(BaseExtractor):
    PLUGIN_NAME = "btc"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_BTC,
            validator=BitcoinValidator.run,
            data_kind=BitcoinAddress.PLUGIN_NAME,
        )


class BitcoinWif(BaseExtractor):
    PLUGIN_NAME = "btc-wif"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_BTC_WIF,
            validator=BitcoinWifValidator.run,
            data_kind=BitcoinWif.PLUGIN_NAME,
        )


class Bip32XKey(BaseExtractor):
    PLUGIN_NAME = "bip32-xkey"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_BIP32_XKEY,
            validator=slip132.address_from_xkey if has_btclib else None,
            data_kind=Bip32XKey.PLUGIN_NAME,
        )


class BitcoinPrivateKey(BaseExtractor):
    PLUGIN_NAME = "btc-privkey"
    PLUGIN_ACTIVE = False

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_BTC_PRIVKEY,
            validator=BitcoinPrivKeyValidator.run,
            data_kind=BitcoinPrivateKey.PLUGIN_NAME,
        )


class EthereumAddressExtractor(BaseExtractor):
    PLUGIN_NAME = "eth"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_ETH,
            validator=EthereumValidator.run,
            data_kind=EthereumAddressExtractor.PLUGIN_NAME,
        )


class LitecoinAddress(BaseExtractor):
    PLUGIN_NAME = "ltc"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_LTC,
            validator=LitecoinValidator.run,
            data_kind=LitecoinAddress.PLUGIN_NAME,
        )


class RippleAddress(BaseExtractor):
    PLUGIN_NAME = "xrp"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_XRP,
            validator=RippleValidator.run,
            data_kind=RippleAddress.PLUGIN_NAME,
        )


class TetherAddress(BaseExtractor):
    PLUGIN_NAME = "usdt"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_USDT,
            validator=TetherValidator.run,
            data_kind=TetherAddress.PLUGIN_NAME,
        )


class BitcoinCashAddress(BaseExtractor):
    PLUGIN_NAME = "bch"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        include_legacy = kwargs.get("include_legacy", True)
        re_ = RE_BCH_WITH_LEGACY if include_legacy else RE_BCH
        yield from _extract_with_regex(
            _input,
            re_,
            validator=BitcoinCashValidator.run,
            data_kind=BitcoinCashAddress.PLUGIN_NAME,
        )


class ChainlinkAddress(BaseExtractor):
    PLUGIN_NAME = "chainlink"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_LINK,
            validator=ChainlinkValidator.run,
            data_kind=ChainlinkAddress.PLUGIN_NAME,
        )


class CardanoAddress(BaseExtractor):
    PLUGIN_NAME = "ada"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_ADA,
            validator=CardanoValidator.run,
            data_kind=CardanoAddress.PLUGIN_NAME,
        )


class PolkadotAddress(BaseExtractor):
    PLUGIN_NAME = "dot"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_DOT,
            validator=PolkadotValidator.run,
            data_kind=PolkadotAddress.PLUGIN_NAME,
        )
