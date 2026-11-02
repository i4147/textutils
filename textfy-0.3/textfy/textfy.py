import os
import time
from twilio.rest import Client


class Textfy:
    def __init__(self):
        _sid = os.environ["TWILIO_SID"]
        _token = os.environ["TWILIO_TOKEN"]
        self._src = os.environ["TWILIO_SRC"]
        self._dst = os.environ["TWILIO_DST"]
        self._twilio_client = Client(_sid, _token)

    def __call__(self, func):
        def wrapper(*args):
            start_time = time.perf_counter()
            kwargs = func(*args)
            end_time = time.perf_counter()
            execution_time = time.gmtime(end_time - start_time)
            msg_body = ["[Task finished]"]
            for k, v in kwargs.items():
                msg_body.append(f"{k}: {v}")
            exec_day = execution_time.tm_mday - 1
            exec_hour = execution_time.tm_hour
            exec_min = execution_time.tm_min
            exec_sec = execution_time.tm_sec
            msg_body.append(f"Exec. time: {exec_day} {exec_hour:02}:{exec_min:02}:{exec_sec:02}")
            msg_body = "\n".join(msg_body)
            self._twilio_client.messages.create(body=msg_body, from_=self._src, to=self._dst)

        return wrapper


def send_msg(msg):
    sid = os.environ["TWILIO_SID"]
    token = os.environ["TWILIO_TOKEN"]
    src = os.environ["TWILIO_SRC"]
    dst = os.environ["TWILIO_DST"]
    twilio_client = Client(sid, token)
    msg_body = ["[Notification]"]
    msg_body.append(msg)
    msg_body = "\n".join(msg_body)
    twilio_client.messages.create(body=msg_body, from_=src, to=dst)
