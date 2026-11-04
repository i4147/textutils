# -*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime

from twilio.rest import Client

name = "Texternet"

"""This is the class that manages communication between the Texternet server and the Twilio API."""


class Texternet:
    pass

    def __init__(self, ACCOUNT_SID, AUTH_TOKEN, PHONENUM):
        self.account_sid = ACCOUNT_SID
        self.auth_token = AUTH_TOKEN
        self.Login = False
        self.username = None
        self.userInfo = None
        self.client = Client(self.account_sid, self.auth_token)
        self.phone_num = PHONENUM

    def getMessages(self, date):
        messages = self.client.messages.list(
            date_sent_after=date,
            to=self.phone_num,
        )
        return messages

    def sendMessage(self, number, msg):
        message = self.client.messages.create(body=msg, from_=self.phone_num, to=number)
        return message.sid

    def sendFile(self, number, file):
        message = self.client.messages.create(
            from_=self.phone_num,
            media_url=file,
            to=number,
        )
        return message.sid


if __name__ == "__main__":
    print("can't run this file.")
