import uuid
from typing import Iterable

from metext.plugin_base import BaseExtractor
from metext.plugins.extractors import _extract_with_regex
from metext.utils.regex import RE_GUID


class UuidExtractor(BaseExtractor):
    PLUGIN_NAME = "uuid"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:

        def validate(value):
            if value.count("-") == 4:
                return True
            value = value.replace("-", "")
            return value[12] in {"0", "1", "2", "3", "4", "5"}

        def get_info(value):
            try:
                res = uuid.UUID(value)
                return {"variant": res.variant, "version": res.version}
            except:
                return None

        def normalize(value):
            value = value.replace(r"-", "").lower()
            return "{}-{}-{}-{}-{}".format(value[:8], value[8:12], value[12:16], value[16:20], value[20:])

        for obj in _extract_with_regex(
            _input,
            RE_GUID,
            per_line=True,
            data_kind=UuidExtractor.PLUGIN_NAME,
            validator=validate,
            postprocess=normalize,
        ):
            info = get_info(obj["value"])
            if not info or info["version"] is None:
                continue
            obj.update({"info": info})
            yield obj
