import re
import json
from datetime import datetime
from lyylog import log
import xml.etree.ElementTree as ET

characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
import time
import lyyre
import Levenshtein
import xpinyin

user_defined_pinyin = {"长虹": "changhong"}


def convert_to_pinyin(text, user_define_pinyin=None):
    pinyin = xpinyin.Pinyin()

    if user_define_pinyin is not None:
        for key, value in user_define_pinyin.items():
            text = text.replace(key, value)

    pinyin_list = []
    for char in text:
        if char.isascii():
            pinyin_list.append(char)
        else:
            pinyin_str = pinyin.get_pinyin(char) if pinyin.get_pinyin(char) else char
            pinyin_list.append(pinyin_str)

    print("pinyin_list=", pinyin_list)
    pinyin_str = "".join(pinyin_list)
    no_tone_pinyin = "".join([p for p in pinyin_str if p not in "āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜüń"])
    return no_tone_pinyin

    if text.isascii():
        print(f"({text})是纯英文")
        pinyin = text

    return pinyin


class TeacherMessageThrottler:
    def __init__(self):
        from collections import defaultdict, deque

        self.messages = defaultdict(deque)

    def _cleanup(self, teacher):
        current_time = time.time()
        while self.messages[teacher] and current_time - self.messages[teacher][0][1] > 60:
            self.messages[teacher].popleft()

    def should_send_message(self, teacher, message):
        self._cleanup(teacher)
        for msg, _ in self.messages[teacher]:
            if are_sentences_similar(msg, message):
                # if msg == message:
                return False
        self.messages[teacher].append((message, time.time()))
        return True


def format_url_in_ocr_text_include_markdown_img(msg_json, text, debug=False):
    old_text = msg_json["markdown"]["text"]
    if debug:
        print("enter format_ocr_text_include_markdown_img")
    url_pattern = r"!\s?\[\s?(?:screenshot)?\s?\]\s?\((http:?//.*\.(bmp)|(png)|(jpg))"

    matches = re.findall(url_pattern, text)
    if len(matches) > 0:
        for match in matches:
            if debug:
                print(match)

            cleaned_url = re.sub(r"\s+", "", match[0])
            if debug:
                print(cleaned_url)
            msg_json["markdown"]["text"] = cleaned_url
            msg_json["img"] = cleaned_url
            print("in foramt_url of lyytext, url ormat finished")
            return msg_json
    else:
        print("in ocr format text=", text)
        msg_json["markdown"]["text"] = text
        msg_json["markdown"]["title"] = text[:30]
        del msg_json["img"]
        print("in format_url_after_ocr of lyytext, 没找到图片包或者 图片链接json= ", msg_json)
        return msg_json


def extract_token(string, debug=False):
    pattern = r"access_token=(.*?)&"
    match = re.search(pattern, string)
    if match:
        access_token = match.group(1)
        if debug:
            print("extract_token result:", access_token)
        return access_token


def are_sentences_similar(sentence1, sentence2, threshold=0.92):
    pattern = re.compile(r"[\u4e00-\u9fa5a-zA-Z0-9]")

    filtered_sentence1 = "".join(pattern.findall(sentence1))
    filtered_sentence2 = "".join(pattern.findall(sentence2))

    similarity = Levenshtein.ratio(filtered_sentence1, filtered_sentence2)

    return similarity >= threshold


def dingding_extract_packet_size(message, deub=False):
    pattern = r"http.*\/(.*)_(\d{2,4}_\d{2,4})"

    match = re.search(pattern, message)
    if match:
        group1 = match.group(1)
        group2 = match.group(2)
        print("group1=", group1, "group2=", group2)
        return group1, group2
    else:
        return None, None


def encode_number(number, debug=False):
    thousands = number // 1024
    remainder = number % 1024
    if debug:
        print("remainder:", remainder)
    sixteens = remainder // 16
    units = remainder % 16
    if debug:
        print("units:", units)
    encoded = characters[thousands] + characters[sixteens] + characters[units * 4 + 1]
    return encoded


def decode_number(encoded, debug=False):
    thousands = characters.index(encoded[0])
    sixteens = characters.index(encoded[1])
    units = int(characters.index(encoded[2]) / 4)

    number = (thousands * 1024) + (sixteens * 16) + units
    if debug:
        print(" in decode_number, number=", number)
    return number


def txt_to_jd_jsontext(msgtype, chinesename, msg_time, txt, return_json=False):
    msg_json = {}
    msg_json["msgtype"] = msgtype
    msg_json["chinesename"] = chinesename
    msg_json["time"] = msg_time
    msg_json["message"] = txt
    if return_json:
        return msg_json
    else:
        return json.dumps(msg_json)


def extract_token(string, debug=False):
    pattern = r"access_token=(.*?)&"
    match = re.search(pattern, string)
    if match:
        access_token = match.group(1)
        if debug:
            print("extract_token result:", access_token)
        return access_token


def read_xml_branch_value(
    xml_file=r"D:\Soft\_Stock\KTPro\User\BlockInfo\UserBlockInfo6633458850865152.data",
    branch_name="BC",
    attribute_name="ToTDX.",
    option="Stock",
):

    with open(xml_file, "r", encoding="utf-16-le") as f:
        tree = ET.parse(f)
    root = tree.getroot()

    for elem in root.iter(branch_name):
        if elem.attrib.get("Name") == attribute_name:
            return elem.attrib.get(option)

    return None


def write_xml_branch_value(
    xml_file=r"D:\Soft\_Stock\KTPro\User\BlockInfo\UserBlockInfo6633458850865152.data",
    branch_name="BC",
    attribute_name="ToTDX.",
    option="Stock",
    new_value="",
    debug=False,
):
    with open(xml_file, "r", encoding="utf-16-le") as f:
        tree = ET.parse(f)
    root = tree.getroot()

    for elem in root.iter(branch_name):
        if elem.attrib.get("Name") == attribute_name:
            elem.attrib[option] = new_value
            break
    tree.write(xml_file, encoding="utf-16-le", xml_declaration=False)
    if debug:
        result = read_xml_branch_value(xml_file, branch_name, attribute_name, option)
        print(
            f"write_xml_branch_value: {xml_file} {branch_name} {attribute_name} {option} {new_value}, result={result}"
        )


def is_ad(text, keywords, threshold):
    count = 0
    for keyword in keywords:
        if keyword in text:
            count += 1
    if count >= threshold:
        return True
    else:
        return False


def ocr_text_not_useful(ocr_result_text, blacklist_latterns):

    if ocr_result_text is None or len(ocr_result_text) == 0:
        print("结果空值，OCR没识别出来")
        return True

    elif deny_ocr_text_patterns(blacklist_latterns, ocr_result_text, debug=False):
        log("包含禁止OCR关键字" + ocr_result_text)
        return True

    elif "http" not in ocr_result_text:
        now = datetime.now()
        clean_text = lyyre.exclude_userfull_number_before_calc(ocr_result_text)
        if count_digits(clean_text) > 20:
            log("数字太多,占比超20%，怕是表格哦。不识别,clean_text" + clean_text)
            return True
    else:
        return False


def get_all_values_in_dict(data):
    values = []
    for key, value in data.items():
        if isinstance(value, dict):
            values.extend(get_all_values_in_dict(value))
        else:
            values.append(str(value))
    return values


def list_include_dict_to_str(words_list):
    print("words_list=", words_list, type(words_list))
    text = ""
    for item in words_list:
        text += item["words"]

    return text


def count_digits(s):
    digits = sum(c.isdigit() for c in s)
    total_length = len(s)
    return (digits / total_length) * 100


def batch_replace_text_by_dict(text, to_replace_dict: dict, debug=False):
    for key, value in to_replace_dict.items():
        text = text.replace(key, value)
    return text


def batch_format_remove_subtext(text: str, to_remove_list: list, debug=False):
    for item in to_remove_list:
        text = text.replace(item, "")
        if debug and item in text:
            print(text, "in batch_format_remove_subtext, 包含:", item)
    return text


def deny_ocr_text_patterns(regex_pattern_list, text, debug=False):
    for regex in regex_pattern_list:
        pattern = re.compile(regex)
        match = pattern.findall(text)
        if len(match) > 0:
            if debug:
                print("in deny_ocr_text_patterns, match=", match)
            return True
        else:
            if debug:
                print("没有匹配,regex=", regex)

    return False


def replace_regex_to_strings(original_text: str, regex_pattern: str, to_replace_text: str = "", debug=False):
    pattern = re.compile(regex_pattern)
    new_str = re.sub(pattern, to_replace_text, original_text)
    if debug:
        matches = re.findall(pattern, original_text)
        if matches:
            print("in replace_regex_to_strings, 匹配的部分：", matches, "子文本替换为: ", to_replace_text)
    return new_str


def batch_remove_regex_strings_by_list(regex_pattern_list, text, debug=False):
    for regex in regex_pattern_list:
        text = replace_regex_to_strings(text, regex, "", debug=debug)
    return text


def batch_replace_by_regex_dict(regex_new_dict: dict, text: str, debug=False):
    for key_regex_str, value_to_replace in regex_new_dict.items():
        text = replace_regex_to_strings(text, key_regex_str, value_to_replace, debug=debug)
    return text


def batch_strip_text(text: str, to_remove_words_list: list, debug: bool = False):
    for words in to_remove_words_list:
        text = text.strip(words)
        if debug:
            if text.startswith(words) or text.endswith(words):
                print("in batch_strip_text, text startwith=" + words)
    return text.strip()


def replace_digits_with_chinese(text):
    mapping = {
        "0": "零",
        "1": "一",
        "2": "二",
        "3": "三",
        "4": "四",
        "5": "五",
        "6": "六",
        "7": "七",
        "8": "八",
        "9": "九",
    }
    replaced_text = ""
    for char in text:
        if char.isdigit():
            replaced_text += mapping[char]
        else:
            replaced_text += char
    return replaced_text


def extract_regex_strings(regex, text):
    pattern = re.compile(regex)

    regex_strings = pattern.findall(text)

    return regex_strings


def clean_text(text):

    pattern = r"(\d{1,2}:\d{1,2}:\d{1,2}[]) ([\u4e00-\u9fa50-9]+) (.*)"

    clean_text = re.sub(pattern, "", text)

    clean_text = re.sub(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", "", clean_text)

    print(clean_text)
    return clean_text


def remove_date_time(texting):
    patterns = [r"\d{2}:\d{2}:\d{2}[ ]?", r"\d{4}-\d{2}-\d{2}[ ]?", r"\d{1,2}:\d{2}:\d{2}"]

    for pattern in patterns:
        texting = re.sub(pattern, "", str(texting))
    return texting


def get_name_from_code(code):
    import lyystkcode

    stock_code_name_dict = lyystkcode.get_code_name_dict()
    code = str(code).zfill(6)
    if code in stock_code_name_dict.keys():
        return f"[{(code)}:{stock_code_name_dict[code]}]"


def add_stockname_for_stkcode(txt):

    def replace(match):
        num = match.group(0)
        start_digit = num[0]
        if start_digit in ["3", "6", "0"]:
            new_num = str(get_name_from_code(int(num)))
            return num.replace(num, new_num)
        else:
            return num

    replaced_text = re.sub(r"\b(?:3|6|0)\d{5}\b", replace, txt)
    # print("toadd_stkname_txt=", txt, "replaced_text=", replaced_text)
    return replaced_text


def num_to_chinese(match):
    num_map = {
        "0": "零",
        "1": "一",
        "2": "二",
        "3": "三",
        "4": "四",
        "5": "五",
        "6": "六",
        "7": "七",
        "8": "八",
        "9": "九",
    }
    return "".join(num_map[digit] for digit in match.group())


def format_to_speak_text(txt):

    txt = re.sub(r"\d{6}", num_to_chinese, txt)

    txt = remove_date_time(txt)
    txt = clean_text(txt)
    return txt


if __name__ == "__main__":
    txt = "2021-09-30 15:00:00 今日首板：15只板：5只三板：1只"
    result = convert_to_pinyin("长虹")
    print(result)
