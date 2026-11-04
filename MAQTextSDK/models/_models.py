# coding=utf-8

import msrest.serialization


class KeyPhraseInput(msrest.serialization.Model):
    _attribute_map = {
        "text": {"key": "text", "type": "str"},
        "keyphrases_count": {"key": "keyphrases_count", "type": "int"},
        "diversity_threshold": {"key": "diversity_threshold", "type": "float"},
        "alias_threshold": {"key": "alias_threshold", "type": "float"},
    }

    def __init__(self, **kwargs):
        super(KeyPhraseInput, self).__init__(**kwargs)
        self.text = kwargs.get("text", None)
        self.keyphrases_count = kwargs.get("keyphrases_count", None)
        self.diversity_threshold = kwargs.get("diversity_threshold", None)
        self.alias_threshold = kwargs.get("alias_threshold", None)


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

    def __init__(self, **kwargs):
        super(KeyPhraseResponseItem, self).__init__(**kwargs)
        self.key_phrase = kwargs["key_phrase"]
        self.score = kwargs["score"]
        self.similar = kwargs["similar"]


class PIIScrubberInput(msrest.serialization.Model):
    _attribute_map = {
        "data": {"key": "data", "type": "str"},
        "entity_list": {"key": "entity_list", "type": "str"},
    }

    def __init__(self, **kwargs):
        super(PIIScrubberInput, self).__init__(**kwargs)
        self.data = kwargs.get("data", None)
        self.entity_list = kwargs.get("entity_list", None)


class PIIScrubberResponse(msrest.serialization.Model):
    _attribute_map = {
        "scrubbed_text": {"key": "scrubbed_text", "type": "str"},
    }

    def __init__(self, **kwargs):
        super(PIIScrubberResponse, self).__init__(**kwargs)
        self.scrubbed_text = kwargs.get("scrubbed_text", None)
