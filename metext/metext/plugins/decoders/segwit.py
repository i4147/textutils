from typing import List, Tuple, Union

from metext.plugin_base import BaseDecoder, Decodable
from metext.plugins.decoders.bech32 import Bech32Decoder


def convert_bits(data, from_bits, to_bits, pad=True):
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << to_bits) - 1
    max_acc = (1 << (from_bits + to_bits - 1)) - 1
    for value in data:
        if value < 0 or (value >> from_bits):
            return None
        acc = ((acc << from_bits) | value) & max_acc
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (to_bits - bits)) & maxv)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & maxv):
        return None
    return ret


class SegwitDecoder(BaseDecoder):
    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Union[Tuple[None, None], Tuple[str, List[int]]]:
        hrp = kwargs.get("hrp", "bc")
        hrpgot, _input = Bech32Decoder.run(_input)
        if hrp and hrpgot != hrp:
            return None, None
        decoded = convert_bits(_input[1:], 5, 8, False)
        if decoded is None or len(decoded) < 2 or len(decoded) > 40:
            return None, None
        if _input[0] > 16:
            return None, None
        if _input[0] == 0 and len(decoded) != 20 and len(decoded) != 32:
            return None, None
        return _input[0], decoded
