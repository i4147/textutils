import requests
import json


class XytextResponse:
    def __init__(self, response):
        try:
            self.raw_response = response
            self.success = response.get("success", False)
            if not self.success:
                self.message = response.get("message", None)
                raise Exception(self.message)
            self.usage = type("Usage", (), response.get("usage", {}))
            self.call_id = response.get("call_id", None)

            result_str = response.get("result")
            if result_str:
                try:
                    self.result = json.loads(result_str)
                except json.JSONDecodeError:
                    self.result = result_str
            else:
                self.result = None
        except Exception as e:
            print("Xytext Error Reason: " + str(e))
            self.success = False
            self.result = None


class Xytext:
    def __init__(self, func_id, stage, auth_token, timeout=900):
        self.base_url = "https://api.xytext.com/invoke"
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {auth_token}"}
        self.func_id = func_id
        self.stage = stage
        self.timeout = timeout

    def invoke(self, input_text, extras=None):
        payload = {"input": input_text, "func_id": self.func_id, "stage": self.stage}
        if extras is not None:
            payload.update(extras)

        response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=self.timeout)
        return XytextResponse(response.json())
