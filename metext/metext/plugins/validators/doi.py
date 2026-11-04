import requests

from metext.plugin_base import BaseValidator


class DoiValidator(BaseValidator):
    PLUGIN_NAME = "doi"

    @classmethod
    def run(cls, _input, **kwargs) -> bool:
        from urllib.error import HTTPError

        if _input.lower().startswith("doi:"):
            _input = _input[4:]

        if not _input.startswith("10."):
            return False

        url = "https://doi.org/api/handles/{doi}".format(doi=_input)

        try:
            result = requests.get(url).json()
        except HTTPError:
            raise ValueError("HTTP 404: DOI not found")

        return any(v["data"]["value"] for v in result["values"] if v.get("type") == "URL")
