# coding=utf-8

from typing import List, Optional

import msrest.serialization


class KeyPhraseInput(msrest.serialization.Model):
    _attribute_map = {
        "text": {"key": "text", "type": "str"},
        "keyphrases_count": {"key": "keyphrases_count", "type": "int"},
        "diversity_threshold": {"key": "diversity_threshold", "type": "float"},
        "alias_threshold": {"key": "alias_threshold", "type": "float"},
    }

    def __init__(
        self,
        *,
        text: Optional[str] = None,
        keyphrases_count: Optional[int] = None,
        diversity_threshold: Optional[float] = None,
        alias_threshold: Optional[float] = None,
        **kwargs,
    ):
        super(KeyPhraseInput, self).__init__(**kwargs)
        self.text = text
        self.keyphrases_count = keyphrases_count
        self.diversity_threshold = diversity_threshold
        self.alias_threshold = alias_threshold


class KeyPhraseResponseItem(msrest.serialization.Model):
    _validation = {
        "key_phrase": {"required": True},
        "score": {"required": True},
        "similar": {"required": True},
    }

    _attribute_map = {
        "key_phrase": {"key": "KeyPhrase", "type": "str"},
        "score": {"key": "Score", "type": "int"},
        "similar": {"key": "Similar", "type": "[str]"},
    }

    def __init__(self, *, key_phrase: str, score: int, similar: List[str], **kwargs):
        super(KeyPhraseResponseItem, self).__init__(**kwargs)
        self.key_phrase = key_phrase
        self.score = score
        self.similar = similar


class PIIScrubberInput(msrest.serialization.Model):
    _attribute_map = {
        "data": {"key": "data", "type": "str"},
        "entity_list": {"key": "entity_list", "type": "str"},
    }

    def __init__(self, *, data: Optional[str] = None, entity_list: Optional[str] = None, **kwargs):
        super(PIIScrubberInput, self).__init__(**kwargs)
        self.data = data
        self.entity_list = entity_list


class PIIScrubberResponse(msrest.serialization.Model):
    _attribute_map = {
        "scrubbed_text": {"key": "scrubbed_text", "type": "str"},
    }

    def __init__(self, *, scrubbed_text: Optional[str] = None, **kwargs):
        super(PIIScrubberResponse, self).__init__(**kwargs)
        self.scrubbed_text = scrubbed_text
