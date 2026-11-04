# -*- coding: utf-8 -*-

import random
from hashlib import md5

import requests

appid = "INPUT_YOUR_APPID"
appkey = "INPUT_YOUR_APPKEY"

endpoint = "http://api.fanyi.baidu.com"
path = "/api/trans/vip/translate"
url = endpoint + path

from_lang = "en"
to_lang = "zh"


# query = 'Hello World! This is 1st paragraph.\nThis is 2nd paragraph.'


def make_md5(s, encoding="utf-8"):
    return md5(s.encode(encoding)).hexdigest()


def translate(query, from_lang="zh", to_lang="en"):
    result = []
    salt = random.randint(32768, 65536)
    sign = make_md5(appid + query + str(salt) + appkey)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"appid": appid, "q": query, "from": from_lang, "to": to_lang, "salt": salt, "sign": sign}

    r = requests.post(url, params=payload, headers=headers)
    trans_result = r.json().get("trans_result", [])
    if trans_result:
        for trans in trans_result:
            dst = trans.get("dst", "")
            result.append(dst)
    return result


def back_translate(query, from_lang="zh"):
    result = []
    if from_lang == "zh":
        to_lang = "en"
    else:
        to_lang = "zh"
    other_lang_result_list = translate(query, from_lang, to_lang)
    for r in other_lang_result_list:
        b = translate(r, from_lang=to_lang, to_lang=from_lang)
        result.append(b)
    return result


if __name__ == "__main__":
    query = "Hello World! This is 1st paragraph.\nThis is 2nd paragraph."
    print(translate(query, from_lang="en", to_lang="zh"))
    query = "你好，度目人脸抓拍机整挺好\n你幸福吗？"
    print(translate(query, from_lang="zh", to_lang="en"))
    print(back_translate(query, from_lang="zh"))
