from metext.plugin_base import BaseValidator
from metext.utils.regex import RE_MD5


class MD5Validator(BaseValidator):
    PLUGIN_NAME = "md5"

    @classmethod
    def run(cls, _input, **kwargs) -> bool:
        return RE_MD5.match(_input) is not None
