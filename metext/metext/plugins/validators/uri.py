from urllib.parse import urlparse

from metext.plugin_base import BaseValidator
from metext.plugins.validators.baseenc import Base64Validator
from metext.utils._torf._magnet import Magnet
from metext.utils.regex import RE_URN
from metext.utils.uri import URI_SCHEMES


class URIValidator(BaseValidator):
    PLUGIN_NAME = "uri"

    @classmethod
    def run(cls, _input, **kwargs) -> bool:
        if len(_input) < 8:
            return False

        strict = kwargs.get("strict", True)
        schemes = kwargs.get("schemes", URI_SCHEMES)
        parsed = urlparse(_input)
        is_path_like = ("/" in parsed.path) if strict else True
        has_selected_scheme = (
            parsed.scheme in schemes and _input.split(":")[0] in [parsed.scheme.lower(), parsed.scheme.upper()]
            if schemes
            else True
        )
        return (
            bool(parsed.netloc) or (bool(parsed.path) and is_path_like) or (bool(parsed.scheme) and bool(parsed.query))
        ) and has_selected_scheme


class URLValidator(BaseValidator):
    PLUGIN_NAME = "url"

    @classmethod
    def run(cls, _input, **kwargs) -> bool:
        return URIValidator.run(_input, schemes=("http", "https", "ftp", "ftps"), **kwargs)


class URNValidator(BaseValidator):
    PLUGIN_NAME = "urn"

    @classmethod
    def run(cls, _input, **kwargs) -> bool:
        match = RE_URN.match(_input)
        return match is not None and match.group(0) == _input


class DataURIValidator(BaseValidator):
    PLUGIN_NAME = "data_uri"

    @classmethod
    def run(cls, _input: str, **kwargs) -> bool:
        parsed = urlparse(_input)
        base64_valid = "base64," not in _input or Base64Validator.run(_input.split("base64,")[-1])
        return parsed.scheme == "data" and bool(parsed.path) and base64_valid


class MagnetValidator(BaseValidator):
    PLUGIN_NAME = "magnet"

    @classmethod
    def run(cls, _input: str, **kwargs) -> bool:
        try:
            Magnet.from_string(_input)
            return True
        except:
            return False
