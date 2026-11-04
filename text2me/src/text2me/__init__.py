# import text2me;text2me.send('消息', '文件路径')

from twilio.rest import Client


def send(msg, config_file):
    with open(config_file) as f:
        account_sid, auth_token, from_phone, to_phone = f.readlines()
    Client(account_sid, auth_token).messages.create(body=msg, from_=from_phone, to=to_phone)
