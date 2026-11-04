from metext.plugin_base import BaseDecoder, Decodable


class IdDecoder(BaseDecoder):
    PLUGIN_NAME = "raw"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Decodable:
        return _input
