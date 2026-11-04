# coding=utf-8

try:
    from .data_input_data_item_py3 import DataInputDataItem
    from .data_input_py3 import DataInput
    from .response_body_item_py3 import ResponseBodyItem
    from ._models_py3 import KeyPhraseInput
    from ._models_py3 import KeyPhraseResponseItem
    from ._models_py3 import PIIScrubberInput
    from ._models_py3 import PIIScrubberResponse
except (SyntaxError, ImportError):
    from .data_input_data_item import DataInputDataItem
    from .data_input import DataInput
    from .response_body_item import ResponseBodyItem
    from ._models import KeyPhraseInput
    from ._models import KeyPhraseResponseItem
    from ._models import PIIScrubberInput
    from ._models import PIIScrubberResponse

__all__ = [
    "DataInputDataItem",
    "DataInput",
    "ResponseBodyItem",
    "KeyPhraseInput",
    "KeyPhraseResponseItem",
    "PIIScrubberInput",
    "PIIScrubberResponse",
]
