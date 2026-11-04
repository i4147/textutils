# coding=utf-8

from msrest.service_client import SDKClient
from msrest import Configuration, Serializer, Deserializer
from .version import VERSION
from msrest.pipeline import ClientRawResponse
from msrest.exceptions import HttpOperationError
from .BatchSetup import BatchSetup
from . import models
import json


class MAQTextAnalyticsLinuxConfiguration(Configuration):
    def __init__(self, base_url=None):

        if not base_url:
            base_url = "https://maqtextnalyticssdk.azure-api.net/text"

        super(MAQTextAnalyticsLinuxConfiguration, self).__init__(base_url)

        self.add_user_agent("maqtextanalyticslinux/{}".format(VERSION))


class MAQTextAnalyticsLinux(SDKClient):
    def __init__(self, base_url=None):

        self.config = MAQTextAnalyticsLinuxConfiguration(base_url)
        super(MAQTextAnalyticsLinux, self).__init__(None, self.config)

        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self.api_version = "1.0"
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

    def post_sentimentclassifier(self, api_key, data_input=None, custom_headers=None, raw=False, **operation_config):
        url = self.post_sentimentclassifier.metadata["url"]

        query_parameters = {}

        header_parameters = {}
        header_parameters["Accept"] = "application/json"
        header_parameters["Content-Type"] = "application/json; charset=utf-8"
        if custom_headers:
            header_parameters.update(custom_headers)
        header_parameters["APIKey"] = self._serialize.header("api_key", api_key, "str")

        inputTransform = BatchSetup(data_input)
        if data_input is not None:
            body_content = self._serialize.body(inputTransform.makeBody(), "DataInput")
        else:
            body_content = None

        request = self._client.post(url, query_parameters, header_parameters, body_content)
        response = self._client.send(request, stream=False, **operation_config)

        if response.status_code not in [200]:
            if "errors" in json.loads(response.text):
                response.reason = json.loads(response.text)["errors"][0]["message"]
                raise HttpOperationError(self._deserialize, response)
            else:
                response.reason = json.loads(response.text)["message"]
                raise HttpOperationError(self._deserialize, response)

        deserialized = None

        if response.status_code == 200:
            results = json.loads(response.text)
            for idx, data in enumerate(body_content["data"]):
                results[idx]["text"] = data["text"]
            return results
            deserialized = self._deserialize("[ResponseBodyItem]", response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized

    post_sentimentclassifier.metadata = {"url": "/SentimentClassifier"}

    def post_piiscrubber(self, api_key, data_input=None, custom_headers=None, raw=False, **operation_config):
        url = self.post_piiscrubber.metadata["url"]

        query_parameters = {}

        header_parameters = {}
        header_parameters["Accept"] = "application/json"
        header_parameters["Content-Type"] = "application/json; charset=utf-8"
        if custom_headers:
            header_parameters.update(custom_headers)
        header_parameters["APIKey"] = self._serialize.header("api_key", api_key, "str")

        try:
            if data_input["entity_list"] and isinstance(data_input["entity_list"], list):
                data_input["entity_list"] = ",".join(data_input["entity_list"])
            else:
                raise Exception
        except:
            raise Exception(
                """InvalidJSONError: Not a valid format. Expected 'entity_list' as a key with list of entities in input json. Please send json in template as such {data: "text here", entity_list: ["entity1", "entity2"]}"""
            )

        if data_input is not None:
            body_content = self._serialize.body(data_input, "PIIScrubberInput")
        else:
            body_content = None

        request = self._client.post(url, query_parameters, header_parameters, body_content)
        response = self._client.send(request, stream=False, **operation_config)

        if response.status_code not in [200]:
            if "errors" in json.loads(response.text):
                response.reason = json.loads(response.text)["errors"][0]["message"]
                raise HttpOperationError(self._deserialize, response)
            else:
                response.reason = json.loads(response.text)["message"]
                raise HttpOperationError(self._deserialize, response)

        deserialized = None

        if response.status_code == 200:
            results = json.loads(response.text)
            return results

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized

    post_piiscrubber.metadata = {"url": "/PIIScrubber"}

    def post_keyphrase_extractor(self, api_key, data_input=None, custom_headers=None, raw=False, **operation_config):
        url = self.post_keyphrase_extractor.metadata["url"]

        query_parameters = {}

        header_parameters = {}
        header_parameters["Accept"] = "application/json"
        header_parameters["Content-Type"] = "application/json; charset=utf-8"
        if custom_headers:
            header_parameters.update(custom_headers)
        header_parameters["APIKey"] = self._serialize.header("api_key", api_key, "str")

        if data_input is not None:
            body_content = self._serialize.body(data_input, "KeyPhraseInput")
        else:
            body_content = None

        request = self._client.post(url, query_parameters, header_parameters, body_content)
        response = self._client.send(request, stream=False, **operation_config)

        if response.status_code not in [200]:
            if "errors" in json.loads(response.text):
                response.reason = json.loads(response.text)["errors"][0]["message"]
                raise HttpOperationError(self._deserialize, response)
            else:
                response.reason = json.loads(response.text)["message"]
                raise HttpOperationError(self._deserialize, response)

        deserialized = None

        if response.status_code == 200:
            results = json.loads(response.text)
            return results

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized

    post_keyphrase_extractor.metadata = {"url": "/KeyPhrase"}
