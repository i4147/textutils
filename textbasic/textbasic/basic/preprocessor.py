__all__ = [
    "word_replace",
    "blank_adjust",
    "remove_line",
    "remove_re",
    "remove_string",
    "remove_emoji",
    "remove_enter",
    "remove_kor",
    "remove_eng",
    "remove_num",
    "len_filter",
    "morpheme",
    "normal",
]

import pandas as pd
import numpy as np
import re
import copy
import json
import importlib.resources as resources
from emoji import core
from konlpy.tag import Okt


import warnings

warnings.filterwarnings("ignore")


def _stop_word_adjust(string):
    if str(string) == "nan":
        return string

    for w in [".", "?", "!"]:
        while True:
            if f"{w} " not in string:
                break
            string = string.replace(f"{w} ", f"{w}")

        while True:
            if f" {w}" not in string:
                break
            string = string.replace(f" {w}", f"{w}")

        string = string.replace(f"{w}", f"{w} ")
        while True:
            if f"{w} {w}" not in string:
                break
            string = string.replace(f"{w} {w}", f"{w}{w}")

    string = string.replace(". ?", ".?")
    string = string.replace("! ?", "!?")
    string = string.replace("? !", "?!")
    string = string.replace("? )", "?)")
    string = string.replace("! )", "!)")

    return string


def _remove_by_re(string, re_remove_list):
    string = str(string)
    for re_remove in re_remove_list:
        string = re.sub(rf"{re_remove}", "", string)
    return string


def _remove_line_by_junk(string, junk_list):
    string = str(string)
    string_split_list = string.split("\n")

    temp_list = []
    for ss in string_split_list:
        for junk in junk_list:
            if junk in ss:
                ss = ""
                break
        temp_list.append(ss)

    # result_string_list = list(map(lambda x: remove_junk_line(x, junk_list), result_string_list))
    result_string = "\n".join(temp_list)
    return result_string


def _remove_by_string(string, remove_string_list):
    for remove_string in remove_string_list:
        string = str(string)
        remove_string = str(remove_string)
        string = string.replace(remove_string, "")
    return string


def _replace_by_string(string, replace_dict):
    for before, after in replace_dict.items():
        if str(string) != "nan":
            string = string.replace(before, after)
    return string


def length_check(string, max_len, min_len):
    string_len = len(string)
    if string_len < min_len or string_len > max_len:
        string = ""
    return string


def zero2none(string):
    string = str(string)
    if len(string) == 0:
        return None
    else:
        return string


# def drop_none(string_list):
#     # 빈 데이터 제거
#     new_string_list = list(map(zero2none, string_list))
#     df = pd.DataFrame(new_string_list, columns=['string'])
#     df = df.dropna(subset=['string'])
#     new_string_list = df['string'].to_list()
#     return new_string_list


def _remove_emoji(string):
    string = core.replace_emoji(string, replace="")
    return string


def _remove_enter(string):
    string = re.sub("[\n]", " ", string)
    return string


def _remove_kor(string):
    string = re.sub(r"[가-힣]", "", string)
    return string


def _remove_eng(string):
    string = re.sub(r"[a-zA-Z]", "", string)
    return string


def _remove_num(string):
    string = re.sub(r"[0-9]", "", string)
    return string


def _adjust_blank(string):
    string = string.replace("\t", " ")
    while True:
        if "  " in string:
            string = string.replace("  ", " ")
        else:
            break
    return string


def _strip_string(string):
    result_string = string.strip()
    return result_string


def remove_by_len(string_list, min_len, max_len):
    string_len_list = list(map(len, string_list))
    df = pd.DataFrame([string_list, string_len_list], index=["string", "len"]).T
    df = df[df["len"] >= min_len]
    df = df[df["len"] <= max_len]
    string_list = df["string"].to_list()
    return string_list


def mapping_join(data):
    new_string = "".join(data)
    return new_string


morpheme_dict = {
    "Noun": "명사",
    "Verb": "동사",
    "Adjective": "형용사",
    "Determiner": "관형사",
    "Adverb": "부사",
    "Conjunction": "접속사",
    "Exclamation": "감탄사",
    "Josa": "조사",
    "PreEmoi": "선어말어미",
    "Eomi": "어미",
    "Suffix": "접미사",
    "Punctuation": "구두점",
    "Foreign": "기호",
    "Alpha": "알파벳",
    "Number": "숫자",
    "KoreanParticle": "한국어자음",
    "Hashtag": "트위터해시태그",
    "ScreenName": "트위터아이디",
    "Email": "이메일",
    "URL": "사이트주소",
    "VerbPrefix": "동사접두사",
    "Modifier": "수정자",
}


def pos_eng2han(eng_pos):
    han_pos = morpheme_dict[eng_pos]
    return han_pos


def morpheme_analysis(string):
    okt = Okt()
    morph_pos_list = okt.pos(string)
    morph_pos_ary = np.array(morph_pos_list)

    morph_ary = np.squeeze(morph_pos_ary[:, :1])
    pos_list = np.squeeze(morph_pos_ary[:, 1:]).tolist()

    if isinstance(pos_list, str):
        morph_ary = [morph_ary]
        pos_list = [pos_list]

    pos_list = list(map(pos_eng2han, pos_list))

    string_split_list = []
    pre_pos = None
    new_string = ""

    for morph, pos in zip(morph_ary, pos_list):
        if pos in ["조사", "구두점", "기호", "접미사"]:
            rep = ""

        elif pos == "명사":
            if pre_pos == "수정자":
                rep = ""
            else:
                rep = " "

        # elif pos == '동사':
        #     if pre_pos == '명사':
        #         rep = ''
        #     else:
        #         rep = ' '

        elif pos == "동사접두사":
            if pre_pos == "동사접두사":
                rep = ""
            else:
                rep = " "

        elif pos == "관형사":
            if pre_pos == "명사":
                rep = ""
            else:
                rep = " "

        else:
            rep = " "
        new_string += f"{rep}{morph}"
        pre_pos = pos

    # print(string)
    new_string = new_string.replace("( ", "(")
    new_string = new_string.replace("(", " (")
    new_string = new_string.replace(" )", ")")
    new_string = new_string.replace(")", ") ")
    new_string = new_string.replace(".", ". ")
    new_string = new_string.strip()
    new_string = _adjust_blank(new_string)

    string_split_list = new_string.split(" ")

    # # ==
    # if '한국어자음' in pos_list:
    #     print(new_string)
    #     df = pd.DataFrame([morph_ary, pos_list]).T
    #     df.to_csv('./temp.csv', index=False, encoding='utf-8-sig')
    #     sys.exit()
    # # ==
    return string_split_list


def word_replace(data_list, dictionary):

    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)

    new_data_list = list(map(lambda x: _replace_by_string(x, dictionary), new_data_list))

    return new_data_list


def blank_adjust(data_list):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)

    # new_data_list = list(map(_stop_word_adjust, new_data_list))

    new_data_list = list(map(_adjust_blank, new_data_list))

    new_data_list = list(map(_strip_string, new_data_list))

    return new_data_list


def remove_line(data_list, junk_list):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)
    new_data_list = list(map(lambda x: _remove_line_by_junk(x, junk_list), new_data_list))
    return new_data_list


def remove_re(data_list, re_list):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)
    new_data_list = list(map(lambda x: _remove_by_re(x, re_list), new_data_list))
    return new_data_list


def remove_string(data_list, remove_list):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)
    new_data_list = list(map(lambda x: _remove_by_string(x, remove_list), new_data_list))
    return new_data_list


def remove_emoji(data_list):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)
    new_data_list = list(map(_remove_emoji, new_data_list))
    return new_data_list


def remove_enter(data_list):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)
    new_data_list = list(map(_remove_enter, new_data_list))
    return new_data_list


def remove_kor(data_list):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)
    new_data_list = list(map(_remove_kor, new_data_list))
    return new_data_list


def remove_eng(data_list):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)
    new_data_list = list(map(_remove_eng, new_data_list))
    return new_data_list


def remove_num(data_list):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)
    new_data_list = list(map(_remove_num, new_data_list))

    return new_data_list


def len_filter(data_list, min_len=0, max_len=5000):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    new_data_list = copy.deepcopy(data_list)
    new_data_list = remove_by_len(string_list=new_data_list, min_len=min_len, max_len=max_len)
    return new_data_list


def morpheme(data_list):
    if not isinstance(data_list, list):
        raise TypeError("data type is not 'list'")
    # raw = copy.deepcopy(data_list)
    morpheme_list = list(map(morpheme_analysis, data_list))
    return morpheme_list


def normal(data_list):
    new_data_list = copy.deepcopy(data_list)

    with resources.open_text("textbasic.basic", "dictionary.json") as file:
        replace_dict = json.load(file)

    # dict_source = __name__
    # dict_path = 'textbasic/basic/dictionary.json'
    # json_data = pkg_resources.resource_string(dict_source, dict_path)
    # replace_dict = json.loads(json_data)
    # with open('textbasic/basic/dictionary.json', 'r', encoding='utf-8-sig') as f:
    #     replace_dict = json.load(f)
    new_data_list = word_replace(new_data_list, dictionary=replace_dict)
    # new_data_list = remove_enter(new_data_list)
    new_data_list = blank_adjust(new_data_list)
    # junk_list = []
    # new_data_list = remove_line(new_data_list, junk_list=junk_list)
    re_list = ["\u200b", "\xa0", "\u3000", "\ufeff"]
    new_data_list = remove_re(new_data_list, re_list)
    # remove_list = []
    # new_data_list = remove_string(new_data_list, remove_list=remove_list)
    new_data_list = remove_emoji(new_data_list)

    # new_data_list = remove_kor(new_data_list)
    # new_data_list = remove_eng(new_data_list)
    # new_data_list = remove_num(new_data_list)
    # new_data_list = len_filter(new_data_list, min_len=0, max_len=5000)
    # new_data_list = morpheme(new_data_list)
    return new_data_list
    # new_string_list = copy.deepcopy(string_list)

    # # 단어 변경
    # if word_replace:
    #     new_string_list = list(map(lambda x:_replace_by_string(x, replace_dict), new_string_list))

    # # 스탑 워드 처리
    # if stop_word_adjust:
    #     new_string_list = list(map(_stop_word_adjust, new_string_list))

    # # junk line 제거
    # if remove_line_by_junk:
    #     new_string_list = list(map(lambda x:_remove_line_by_junk(x, junk_list), new_string_list))

    # # 정규식(re) 기반 제거
    # if remove_by_re:
    #     new_string_list = list(map(lambda x:_remove_by_re(x, re_list), new_string_list))

    # # 문장 일치 기반 제거
    # if remove_by_string:
    #     new_string_list = list(map(lambda x:_remove_by_string(x, remove_string_list), new_string_list))

    # # 일반 전처리
    # if remove_emoji:
    #     new_string_list = list(map(def_remove_emoji, new_string_list))
    # if remove_enter:
    #     new_string_list = list(map(def_remove_enter, new_string_list))
    # if remove_kor:
    #     new_string_list = list(map(def_remove_kor, new_string_list))
    # if remove_eng:
    #     new_string_list = list(map(def_remove_eng, new_string_list))
    # if remove_num:
    #     new_string_list = list(map(def_remove_num, new_string_list))
    # if adjust_blank:
    #     new_string_list = list(map(def_adjust_blank, new_string_list))
    # if strip_string:
    #     new_string_list = list(map(def_strip_string, new_string_list))

    # # 길이 필터링
    # if len_filter:
    #     new_string_list = remove_by_len(
    #         string_list=new_string_list,
    #         min_len=min_len,
    #         max_len=max_len
    #     )

    # # 형태소 분석
    # if morpheme:
    #     morpheme_list = list(map(morpheme_analysis, new_string_list))
    #     return new_string_list, morpheme_list

    # return data_list
