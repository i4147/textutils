import argparse
import copy
import itertools
import os
import re
from collections import Counter
from datetime import date
import json
from tokenize import String

import nltk
from konlpy.tag import Mecab
from krwordrank.word import KRWordRank
from nltk.corpus import stopwords

from SmiToText.tokenizer.nltk import nltkSentTokenizer
from SmiToText.util.util import Util

all_stop_word = [
    "가령",
    "각각",
    "각자",
    "각종",
    "같다",
    "같이",
    "거니와",
    "거바",
    "거의",
    "것들",
    "게다가",
    "게우다",
    "겨우",
    "결국",
    "경우",
    "고로",
    "곧바로",
    "과연",
    "관하여",
    "관한",
    "그동안",
    "그들",
    "그때",
    "그래",
    "그래도",
    "그래서",
    "그러나",
    "그러니",
    "그러면",
    "그런데",
    "그런즉",
    "그럼",
    "그렇지",
    "그리고",
    "그위에",
    "그저",
    "근거로",
    "기대여",
    "기타",
    "까악",
    "까지",
    "까지도",
    "꽈당",
    "끙끙",
    "끼익",
    "남들",
    "남짓",
    "너희",
    "너희들",
    "놀라다",
    "누구",
    "니다",
    "다른",
    "다만",
    "다소",
    "다수",
    "다음",
    "다음에",
    "단지",
    "답다",
    "당신",
    "당장",
    "대하면",
    "대하여",
    "대한",
    "대해서",
    "댕그",
    "더구나",
    "더라도",
    "더불어",
    "더욱더",
    "동시에",
    "동안",
    "된이상",
    "둥둥",
    "뒤따라",
    "뒤이어",
    "든간에",
    "등등",
    "딩동",
    "따라",
    "따라서",
    "따위",
    "때론",
    "때문",
    "때문에",
    "또한",
    "뚝뚝",
    "로부터",
    "로써",
    "마저",
    "마저도",
    "마치",
    "만약",
    "만약에",
    "만일",
    "만큼",
    "매번",
    "몇몇",
    "모두",
    "모든",
    "무렵",
    "무슨",
    "무엇",
    "물론",
    "바로",
    "반대로",
    "반드시",
    "버금",
    "보다더",
    "보드득",
    "본대로",
    "봐라",
    "부터",
    "붕붕",
    "비교적",
    "비로소",
    "비록",
    "비하면",
    "뿐이다",
    "삐걱",
    "설령",
    "설마",
    "설사",
    "소생",
    "소인",
    "습니까",
    "습니다",
    "시각",
    "시간",
    "시초에",
    "시키다",
    "실로",
    "심지어",
    "아니",
    "아니면",
    "아래윗",
    "아무도",
    "아야",
    "아울러",
    "아이",
    "아이고",
    "아이구",
    "아이야",
    "아이쿠",
    "아하",
    "알았어",
    "앞에서",
    "앞의것",
    "약간",
    "양자",
    "어느",
    "어느것",
    "어느곳",
    "어느때",
    "어느쪽",
    "어느해",
    "어디",
    "어때",
    "어떠한",
    "어떤",
    "어떤것",
    "어떻게",
    "어떻해",
    "어이",
    "어째서",
    "어쨋든",
    "어찌",
    "언제",
    "언젠가",
    "얼마",
    "얼마간",
    "얼마나",
    "얼마큼",
    "없는",
    "엉엉",
    "에게",
    "에서",
    "여기",
    "여러분",
    "여보시오",
    "여부",
    "여전히",
    "여차",
    "연관되다",
    "연이서",
    "영차",
    "옆사람",
    "예컨대",
    "예하면",
    "오로지",
    "오르다",
    "오자마자",
    "오직",
    "오호",
    "오히려",
    "와르르",
    "와아",
    "왜냐하면",
    "외에도",
    "요만큼",
    "요만한걸",
    "요컨대",
    "우르르",
    "우리",
    "우리들",
    "우선",
    "운운",
    "위하여",
    "위해서",
    "윙윙",
    "으로",
    "으로서",
    "으로써",
    "응당",
    "의거하여",
    "의지하여",
    "의해",
    "의해되다",
    "의해서",
    "이 되다",
    "이 밖에",
    "이 외에",
    "이것",
    "이곳",
    "이다",
    "이때",
    "이라면",
    "이래",
    "이러한",
    "이런",
    "이렇구나",
    "이리하여",
    "이만큼",
    "이번",
    "이봐",
    "이상",
    "이어서",
    "이었다",
    "이외에도",
    "이용하여",
    "이젠",
    "이지만",
    "이쪽",
    "이후",
    "인젠",
    "일것이다",
    "일단",
    "일때",
    "일지라도",
    "입각하여",
    "입장에서",
    "잇따라",
    "있다",
    "자기",
    "자기집",
    "자마자",
    "자신",
    "잠깐",
    "잠시",
    "저것",
    "저것만큼",
    "저기",
    "저쪽",
    "저희",
    "전부",
    "전자",
    "전후",
    "제각기",
    "제외하고",
    "조금",
    "조차",
    "조차도",
    "졸졸",
    "좋아",
    "좍좍",
    "주룩주룩",
    "중에서",
    "중의하나",
    "즈음하여",
    "즉시",
    "지든지",
    "지만",
    "지말고",
    "진짜로",
    "쪽으로",
    "차라리",
    "참나",
    "첫번째로",
    "총적으로",
    "최근",
    "콸콸",
    "쾅쾅",
    "타다",
    "타인",
    "탕탕",
    "토하다",
    "통하여",
    "통해",
    "틈타",
    "펄렁",
    "하게하다",
    "하겠는가",
    "하구나",
    "하기에",
    "하나",
    "하느니",
    "하는것도",
    "하는바",
    "하더라도",
    "하도다",
    "하든지",
    "하마터면",
    "하면된다",
    "하면서",
    "하물며",
    "하여금",
    "하여야",
    "하자마자",
    "하지마",
    "하지마라",
    "하지만",
    "하하",
    "한 후",
    "한다면",
    "한데",
    "한마디",
    "한편",
    "한항목",
    "할때",
    "할만하다",
    "할망정",
    "할뿐",
    "할수있다",
    "할수있어",
    "할줄알다",
    "할지라도",
    "할지언정",
    "함께",
    "해도된다",
    "해도좋다",
    "해봐요",
    "해야한다",
    "해요",
    "했어요",
    "향하다",
    "향하여",
    "향해서",
    "허걱",
    "허허",
    "헉헉",
    "혹시",
    "혹은",
    "혼자",
    "훨씬",
    "휘익",
    "힘입어",
    "네이버 메인",
    "말했다",
    "못했다는",
    "대해",
    "현산",
    "위한",
    "충분히",
    "\\n",
    "것도",
    "했다",
    "있는",
    "제공받지",
    "없다",
    "이날오전",
    "하고",
    "이날만기",
    "배포금지",
    "함수추가",
    "무단전재",
    "본문내용",
    "news",
    "머니투데이",
    "어떻",
    "당시",
    "그러면서",
    "받아보",
    "가진",
    "것이",
    "네이버연합뉴스",
    "오늘",
    "내일",
    "모레",
    "어제",
    "그제",
    "오전",
    "오후",
    "구독클릭",
    "부여스마트",
    "공감언론",
    "소재나이스",
    "channa224",
    "com▶[",
]


def in_dict(dict_data, key):
    try:
        if dict_data[key] >= 0:
            return True
    except:
        return False


def check_en_stopword(word):
    stop_words = set(stopwords.words("english"))

    stop_words.add("th")
    if str(word).lower() in stop_words:
        return True
    else:
        return False


def expect_multi_noun_text_en(sentence):

    grammar = """
     NPBAR:
        {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
     NP:
        {<NBAR>}
        {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
    """
    postagged_sentence = nltk.pos_tag(sentence.split())
    nltk_rexp_parser = nltk.RegexpParser(grammar)
    chunks_sentence = nltk_rexp_parser.parse(postagged_sentence)

    extract_noun = []
    extract_noun_score = {}
    for subtree in chunks_sentence.subtrees():
        if subtree.label().startswith("NP"):
            if len(" ".join([a for (a, b) in subtree.leaves()])) > 1:
                noun = " ".join([a for (a, b) in subtree.leaves()])

                extract_noun.append(noun)

                if not in_dict(extract_noun_score, noun):
                    check_capitalize_score = 1000 * len(re.findall("[A-Z]+", noun)) / len(noun.replace(" ", ""))
                    extract_noun_score[noun] = 0.75 + check_capitalize_score
                else:
                    extract_noun_score[noun] += 0.75

    return sorted_dict(extract_noun_score)


def expect_multi_noun_text_ko(sentence):

    grammar = r"""
    SL복합명사1: {<SL>*<S.*>}
    SL복합명사1: {<SN>*<S.*>}

    복합명사1: {<NNG>*<NNG>?}
    복합명사2: {<SN><NN.*>*<X.*>?}
    복합명사3: {<NNG>*<X.*>?}
    복합명사4: {<N.*>*<Suffix>?}   


    동사구: {<NP\+VCP\+EF>}
    동사구: {<NP><VCP\+EF>}
    형용사: {<MA.*>*}
    """
    mecab = Mecab()

    postagged_sentence = mecab.pos(sentence)
    nltk_rexp_parser = nltk.RegexpParser(grammar)
    chunks_sentence = nltk_rexp_parser.parse(postagged_sentence)

    extract_noun = []
    extract_noun_score = {}
    extract_sl_noun_score = {}
    for subtree in chunks_sentence.subtrees():
        noun = " ".join([a for (a, b) in subtree.leaves()])
        if subtree.label().startswith("복합명사"):
            if len(noun) > 1:
                if re.search(r"\s", noun):
                    extract_noun.append(noun)

                    if not in_dict(extract_noun_score, noun):
                        check_capitalize_score = 1000 * len(re.findall("[A-Z]+", noun)) / len(noun.replace(" ", ""))
                        extract_noun_score[noun] = 0.75 + check_capitalize_score
                    else:
                        extract_noun_score[noun] += 0.75
        elif subtree.label().startswith("SL복합명사"):
            _, extract_sl_noun_score = expect_multi_noun_text_en(noun)

        extract_noun_score.update(extract_sl_noun_score)
    return sorted_dict(extract_noun_score)


def expect_single_noun_text_ko(sentence):

    grammar = r"""
    명사1: {<SL>}
    명사1: {<SN>}

    명사1: {<NNG>}
    명사2: {<NN.*>}


    동사구: {<NP\+VCP\+EF>}
    동사구: {<NP><VCP\+EF>}
    형용사: {<MA.*>*}
    """
    mecab = Mecab()

    postagged_sentence = mecab.pos(sentence)
    nltk_rexp_parser = nltk.RegexpParser(grammar)
    chunks_sentence = nltk_rexp_parser.parse(postagged_sentence)

    extract_noun = []
    extract_noun_score = {}
    for subtree in chunks_sentence.subtrees():
        if subtree.label().startswith("명사"):
            if len(" ".join((e[0] for e in list(subtree)))) > 1:
                noun = " ".join((e[0] for e in list(subtree)))
                if re.search(r"\s", noun):
                    extract_noun.append(noun)

                    if not in_dict(extract_noun_score, noun):
                        check_capitalize_score = 1000 * len(re.findall("[A-Z]+", noun)) / len(noun.replace(" ", ""))
                        extract_noun_score[noun] = 0.75 + check_capitalize_score
                    else:
                        extract_noun_score[noun] += 0.75

    return sorted_dict(extract_noun_score)


def cleaning_multi_noun(multi_noun_list=[], multi_noun_list_score=[], cleaning_count=2):
    multi_noun_list = copy.deepcopy(multi_noun_list)
    cleaning_multi_noun_counter = Counter({})

    for multi_noun in multi_noun_list:
        multi_noun = re.sub(r"[\s]+", " ", multi_noun)
        isOnlyEngNum = re.sub("[a-zA-Z0-9]", "", multi_noun)

        if len(isOnlyEngNum.strip()) == 0:
            multi_noun = re.sub(r"[\s]+", " ", multi_noun)
            if len(multi_noun_list_score) == 0:
                if not in_dict(cleaning_multi_noun_counter, multi_noun):
                    check_capitalize_score = (
                        1000 * len(re.findall("[A-Z]+", multi_noun)) / len(multi_noun.replace(" ", ""))
                    )
                    cleaning_multi_noun_counter[multi_noun] = 0.75 + check_capitalize_score
                else:
                    cleaning_multi_noun_counter[multi_noun] += 0.75
                continue
            else:
                if in_dict(cleaning_multi_noun_counter, multi_noun) == False:
                    cleaning_multi_noun_counter[multi_noun] = multi_noun_list_score[multi_noun]
                else:
                    cleaning_multi_noun_counter[multi_noun] += multi_noun_list_score[multi_noun]
                continue

        multi_noun_space_splitter = multi_noun.split(" ")
        if len(multi_noun_space_splitter) >= 1:
            candidate_multi_noun = ""
            for index in range(cleaning_count):
                if len(multi_noun_space_splitter[-1]) == 1:
                    candidate_multi_noun = " ".join(multi_noun_space_splitter[:-1])
                elif len(multi_noun_space_splitter[0]) == 1:
                    candidate_multi_noun = " ".join(multi_noun_space_splitter[1:])
                else:
                    candidate_multi_noun = " ".join(multi_noun_space_splitter)
                multi_noun_space_splitter = candidate_multi_noun.split(" ")

            if candidate_multi_noun.strip() != "":
                if re.search(r"\s", candidate_multi_noun):
                    if len(multi_noun_list_score) == 0:
                        if not in_dict(cleaning_multi_noun_counter, candidate_multi_noun):
                            check_capitalize_score = (
                                1000
                                * len(re.findall("[A-Z]+", candidate_multi_noun))
                                / len(candidate_multi_noun.replace(" ", ""))
                            )
                            cleaning_multi_noun_counter[candidate_multi_noun] = 0.75 + check_capitalize_score
                        else:
                            cleaning_multi_noun_counter[candidate_multi_noun] += 0.75
                    else:
                        if not in_dict(cleaning_multi_noun_counter, candidate_multi_noun):
                            cleaning_multi_noun_counter[candidate_multi_noun] = multi_noun_list_score[
                                candidate_multi_noun
                            ]
                        else:
                            cleaning_multi_noun_counter[candidate_multi_noun] += multi_noun_list_score[
                                candidate_multi_noun
                            ]
                else:
                    if not in_dict(cleaning_multi_noun_counter, candidate_multi_noun):
                        check_capitalize_score = (
                            1000
                            * len(re.findall("[A-Z]+", candidate_multi_noun))
                            / len(candidate_multi_noun.replace(" ", ""))
                        )
                        cleaning_multi_noun_counter[candidate_multi_noun] = 0.75 + check_capitalize_score
                    else:
                        cleaning_multi_noun_counter[candidate_multi_noun] += 0.75

    return cleaning_multi_noun_counter


def krwordrank_noun(sentence_list=[], min_count=5, max_length=10, beta=0.85, max_iter=10, verbose=False):
    krword_rank_noun_counter = Counter({})
    wordrank_extractor = KRWordRank(min_count, max_length, verbose)
    try:
        keywords, rank, graph = wordrank_extractor.extract(sentence_list, beta, max_iter)
        for word, r in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[: len(keywords)]:
            word = re.sub(r"[\s]+", " ", word)
            if len(word) > 1 and isinstance(word.strip(), (int, float)) is False:
                word_cleansing = word[0:-1] + re.sub(
                    "[-=+,#/\\?:^$.@*\"※~&%ㆍ!”』\\‘|\\(\\)\\[\\]\\<\\>`'…》\\^\\)\\(▶]", "", word[-1]
                )
                word_cleansing = word_cleansing.strip()
                if len(word_cleansing) == len(word):
                    krword_rank_noun_counter.update({word: r})
        return krword_rank_noun_counter
    except Exception as e:
        return krword_rank_noun_counter


def remove_stopword(multi_noun_counter, stop_word=[]):
    result_multi_noun_count = Counter({})

    if len(stop_word) == 0 or stop_word == None:
        stop_word = copy.deepcopy(all_stop_word)
    stop_word.extend(stopwords.words("english"))
    stop_word.append("th")
    stop_word.append("Th")
    for multi_noun, count in multi_noun_counter.items():
        if (
            multi_noun not in stop_word
            and not Util().is_int(multi_noun)
            and not str(multi_noun).endswith("니다")
            and not str(multi_noun).endswith("이다")
        ):
            result_multi_noun_count.update({multi_noun: count})

    return result_multi_noun_count


def check_stopword(multi_noun_counter, stop_word=[]):
    if len(stop_word) == 0 or stop_word is None:
        stop_word = all_stop_word
    check_multi_noun_counter = Counter({})

    for noun in multi_noun_counter:
        if (
            len(set(stop_word).difference(noun.split())) == len(stop_word)
            and len(set(stop_word).difference([noun.replace(" ", "")])) == len(stop_word)
            and not Util().is_int(noun)
            and not str(noun).endswith("니다")
            and not str(noun).endswith("이다")
        ):
            check_multi_noun_counter[noun] = multi_noun_counter[noun]

    return check_multi_noun_counter


def check_int_or_float(input):
    try:
        int(input)

        return True
    except:
        try:
            float(input)

            return True
        except:
            return False


def check_all_number(multi_noun_counter):
    check_multi_noun_counter = Counter({})
    for noun in multi_noun_counter:
        if check_int_or_float(noun.strip()) is False:
            check_multi_noun_counter[noun] = multi_noun_counter[noun]
    return check_multi_noun_counter


def check_short_word(multi_noun_counter, limit_len=2):
    check_multi_noun_counter = Counter({})
    for noun in multi_noun_counter:
        noun_len = len(noun.strip())
        if noun_len <= limit_len:
            lower_char_len = len(re.findall("[a-z]", noun))
            if noun_len != lower_char_len:
                check_multi_noun_counter[noun] = multi_noun_counter[noun]
        else:
            check_multi_noun_counter[noun] = multi_noun_counter[noun]
    return check_multi_noun_counter


def remove_last_one_char(multi_noun_counter):
    check_multi_noun_counter = Counter({})

    for noun in multi_noun_counter:
        temp_noun = noun.split(" ")
        if len(temp_noun[0]) == 1:
            check_multi_noun_counter.update({" ".join(temp_noun[1:]): multi_noun_counter[noun]})
        elif len(temp_noun[-1]) == 1:
            check_multi_noun_counter.update({" ".join(temp_noun[:-1]): multi_noun_counter[noun]})
        else:
            check_multi_noun_counter.update({noun: multi_noun_counter[noun]})
    return check_multi_noun_counter


def sorted_dict(multi_noun_score):
    ret_check_multi_noun = []
    ret_check_multi_noun_score = {}
    for noun, r in sorted(multi_noun_score.items(), key=lambda x: x[1], reverse=True)[: len(multi_noun_score)]:
        if r > 0:
            ret_check_multi_noun.append(noun)
            ret_check_multi_noun_score[noun] = r

    return ret_check_multi_noun, ret_check_multi_noun_score


def multi_noun_remove_special_char(multi_noun_counter):
    result_multi_noun = Counter({})

    for multi_noun, count in multi_noun_counter.items():
        temp_multi_noun = re.sub(r"[\s]+", " ", multi_noun)
        if len(temp_multi_noun) > 1:
            temp_multi_noun = temp_multi_noun[0:-1] + re.sub(
                "[-=+,#/\\?:^$.@*\"※~&%ㆍ!”』\\‘|\\(\\)\\[\\]\\<\\>`'…》\\^\\)\\(▶]", "", temp_multi_noun[-1]
            )
            temp_multi_noun = (
                re.sub("[-=+,#/\\?:^$.@*\"※~&%ㆍ!”』\\‘|\\(\\)\\[\\]\\<\\>`'…》\\^\\)\\(▶]", "", temp_multi_noun[0])
                + temp_multi_noun[1:]
            )
        result_multi_noun.update({temp_multi_noun: count})
    return result_multi_noun


def with_word_add_score(multi_noun_counter):
    add_multi_noun_score = Counter({})
    for multi_noun_1, count_1 in multi_noun_counter.items():
        for multi_noun_2, count_2 in multi_noun_counter.items():
            if multi_noun_1 == multi_noun_2:
                continue
            else:
                if len(multi_noun_1) > len(multi_noun_2):
                    if multi_noun_1.find(multi_noun_2):
                        add_multi_noun_score.update({multi_noun_1: count_2})
                else:
                    if multi_noun_2.find(multi_noun_1):
                        add_multi_noun_score.update({multi_noun_2: count_1})
    result_multi_noun_counter = multi_noun_counter + add_multi_noun_score
    return result_multi_noun_counter


def upper_char_add_score(multi_noun_counter):
    result_multi_noun = Counter({})
    for multi_noun, count in multi_noun_counter.items():
        check_capitalize_multi_noun_socre = 0
        if len(re.findall("[A-Z]", multi_noun)) > 0:
            multi_noun_token = multi_noun.split(" ")
            if len(multi_noun_token) > 1:
                token_first_upper_check_counter = 0
                for multi_noun_token_word in multi_noun_token:
                    if len(re.findall("[A-Z]+", multi_noun_token_word[0])) == 1:
                        token_first_upper_check_counter += 1
                if token_first_upper_check_counter == len(multi_noun_token):
                    check_capitalize_multi_noun_socre = 10000

            if check_capitalize_multi_noun_socre != 10000:
                check_capitalize_multi_noun_socre = 10000 * (
                    len(re.findall("[A-Z]", multi_noun)) / len(multi_noun.replace(" ", ""))
                )
            result_multi_noun[multi_noun] = count + check_capitalize_multi_noun_socre
    result_multi_noun = result_multi_noun + multi_noun_counter
    return result_multi_noun


def check_with_in_text(text, multi_noun_counter):
    text_token = text.split(" ")
    result_multi_noun = Counter({})
    for multi_noun, count in multi_noun_counter.items():
        if len(multi_noun.split(" ")) == 1:
            if multi_noun in text_token:
                result_multi_noun.update({multi_noun: count})
        else:
            result_multi_noun.update({multi_noun: count})
    return result_multi_noun


def text_in_mult_noun_finder(multi_noun, multi_noun_score, text):
    text_in_multi_noun = []
    text_in_multi_noun_score = {}
    for noun in multi_noun:
        max_try = len(noun.split(" "))
        for try_count_1 in range(0, max_try):
            try_count_1_text = " ".join(noun.split(" ")[:try_count_1])
            try_count_2_text = " ".join(noun.split(" ")[try_count_1:])
            for try_count_2 in range(0, (max_try - try_count_1)):
                find_multi_noun = try_count_1_text + str(try_count_2_text).replace(" ", "", try_count_2)
                if text.find(find_multi_noun) >= 0:
                    if find_multi_noun not in text_in_multi_noun_score.keys():
                        text_in_multi_noun.append(find_multi_noun)
                        text_in_multi_noun_score[find_multi_noun] = multi_noun_score[noun]

    text_in_noun_result = copy.deepcopy(text_in_multi_noun)
    text_in_noun_result_score = copy.deepcopy(text_in_multi_noun_score)

    for index, noun in enumerate(text_in_noun_result):
        start_position = text.find(noun)

        if start_position > 0:
            prefix_char = ""
            for position in range(start_position - 1, 0, -1):
                if text[position] != " ":
                    prefix_char = text[position] + prefix_char
                else:
                    break

            if re.sub(r"[가-힣·\s]", "", prefix_char) == "" and prefix_char.strip() != "":
                text_in_noun_result_score[prefix_char + noun] = text_in_multi_noun_score[noun]
                text_in_noun_result_score[noun] = 0
            else:
                text_in_noun_result_score[noun] = text_in_multi_noun_score[noun]

    text_in_multi_noun_result, text_in_multi_noun_result_score = sorted_dict(text_in_noun_result_score)
    text_in_multi_noun_result, text_in_multi_noun_result_score = check_stopword(
        text_in_multi_noun_result, text_in_multi_noun_result_score
    )

    return sorted_dict(text_in_multi_noun_result_score)


def text_inside_check(text, multi_noun_counter):
    multi_noun_counter_result = Counter({})

    text = text.strip()
    for multi_noun, count in multi_noun_counter.items():
        if len(text) > 0:
            start_point = text.find(multi_noun)
            end_point = start_point + len(multi_noun)
            if start_point > 0 and text[start_point - 1] == " ":
                multi_noun_counter_result.update({multi_noun: count})

    return multi_noun_counter_result


def check_noisy(multi_noun_counter, remove_char="—"):
    multi_noun_counter_result = Counter({})
    for multi_noun, count in multi_noun_counter.items():
        clean_multi_noun = str(multi_noun.strip())
        if len(clean_multi_noun) > 1:
            if clean_multi_noun.startswith(remove_char):
                remove_start_index = 0
                for index, char in enumerate(clean_multi_noun):
                    if char == remove_char:
                        remove_start_index = index
                    else:
                        break
                if remove_start_index < len(clean_multi_noun):
                    remove_start_index_noun = clean_multi_noun[remove_start_index + 1 :]
                else:
                    remove_start_index_noun = clean_multi_noun[remove_start_index + 1 :]

                if len(remove_start_index_noun) > 1:
                    multi_noun_counter_result.update({remove_start_index_noun: count})
            else:
                if len(clean_multi_noun) > 1:
                    multi_noun_counter_result.update({multi_noun.strip(): count})
    return multi_noun_counter_result


def remove_one_char(multi_noun_counter):
    multi_noun_counter_result = Counter({})

    for multi_noun, count in multi_noun_counter.items():
        clean_multi_noun = str(multi_noun.strip())
        clean_multi_none_token = clean_multi_noun.split(" ")

        if len(clean_multi_noun) >= 1 and len(clean_multi_none_token) > 0:
            temp_clean_multi_none = ""
            if len(clean_multi_none_token[0]) == 1 and len(clean_multi_none_token[-1]) == 1:
                temp_clean_multi_none = " ".join(clean_multi_none_token[1:-1]).strip()
            elif len(clean_multi_none_token[0]) == 1:
                temp_clean_multi_none = " ".join(clean_multi_none_token[1:]).strip()
            elif len(clean_multi_none_token[-1]) == 1:
                temp_clean_multi_none = " ".join(clean_multi_none_token[:-1]).strip()
            else:
                temp_clean_multi_none = clean_multi_noun
            multi_noun_counter_result.update({temp_clean_multi_none: count})
    return multi_noun_counter_result


def remove_first_last_char(multi_noun_counter, loop=1):
    for i in range(0, loop):
        multi_noun_counter = remove_one_char(multi_noun_counter)
    return multi_noun_counter


def extract_mecab_multi_noun(text, item_counter=0):
    text = text.strip()

    multi_noun_counter = Counter({})
    krword_rank_noun_counter = Counter({})
    krword_rank_once_noun_counter = Counter({})
    if text:
        sentence_list = nltkSentTokenizer(text)

        for sentence in sentence_list:
            sentence = sentence.strip()
            if sentence:
                first_multi_noun_list, _ = expect_multi_noun_text_ko(sentence)
                first_single_noun_list, _ = expect_single_noun_text_ko(sentence)

                first_multi_noun_list.extend(first_single_noun_list)

                second_multi_noun_counter = cleaning_multi_noun(first_multi_noun_list, cleaning_count=2)

                multi_noun_counter.update(second_multi_noun_counter)

                temp_noun = copy.deepcopy(multi_noun_counter)
                for n in temp_noun:
                    if len(n.strip()) > 1 and n.find(" ") < 0:
                        start_position = sentence.find(n)
                        if start_position > 0:
                            start_position = start_position - 1
                        end_position = start_position + len(n)
                        if len(sentence) > end_position and sentence[end_position] != " ":
                            end_position = sentence.find(" ", end_position + 1, len(sentence))
                            word = sentence[start_position:end_position].strip()
                            if len(word) > 1 and isinstance(word.strip(), (int, float)) is False:
                                word_cleansing = word[0:-1] + re.sub(
                                    "'\\([-=+,#/\\?:^$.@*\"※~&%ㆍ!”』\\‘|\\(\\)\\[\\]\\<\\>`'…》\\^\\)\\(▶]",
                                    "",
                                    word[-1],
                                )
                            else:
                                word_cleansing = re.sub(
                                    "'\\([-=+,#/\\?:^$.@*\"※~&%ㆍ!”』\\‘|\\(\\)\\[\\]\\<\\>`'…》\\^\\)\\(▶]", "", word
                                )

                            multi_noun_counter.update({word_cleansing: 0.75})
                        else:
                            word = sentence[start_position:end_position].strip()
                            multi_noun_counter.update({word: 0.75})

        multi_noun_counter = check_stopword(multi_noun_counter)

        krword_rank_noun_counter = krwordrank_noun(sentence_list=sentence_list, min_count=5)
        krword_rank_noun_counter = check_stopword(krword_rank_noun_counter)

        krword_rank_once_noun_counter = krwordrank_noun(sentence_list=sentence_list, min_count=2)
        krword_rank_once_noun_counter = check_stopword(krword_rank_once_noun_counter)

    multi_noun_counter.update(krword_rank_noun_counter)
    multi_noun_counter.update(krword_rank_once_noun_counter)

    multi_noun_counter = with_word_add_score(multi_noun_counter)

    multi_noun_counter = remove_stopword(multi_noun_counter)
    multi_noun_counter = check_short_word(multi_noun_counter, limit_len=3)
    multi_noun_counter = check_all_number(multi_noun_counter)
    multi_noun_counter = multi_noun_remove_special_char(multi_noun_counter)

    multi_noun_counter = check_noisy(multi_noun_counter)
    multi_noun_counter = check_noisy(multi_noun_counter, remove_char="–")
    multi_noun_counter = remove_first_last_char(multi_noun_counter, loop=2)

    return multi_noun_counter


def extract_file_multi_noun(input, output, item_counter=0):
    input_file = open(input, mode="r", encoding="utf-8")
    open(output, mode="w", encoding="utf-8")
    output_file = open(output, mode="a", encoding="utf-8")
    line_number = 1
    while True:
        line = input_file.readline()
        if not line:
            break

        _, line_array_multi_noun_score_sorted = extract_multi_noun(line, item_counter=item_counter)
        line_array_multi_noun_score_sorted_json = json.dumps(line_array_multi_noun_score_sorted, ensure_ascii=False)
        output_file.write(str(line_array_multi_noun_score_sorted_json) + os.linesep)
        print(line_number, line_array_multi_noun_score_sorted_json)
        line_number += 1


def extract_multi_noun(text, item_counter=0):
    text = text.strip()
    multi_noun_counter_result = Counter({})
    for text_array in text.split("\n"):
        text_array = text_array.strip()

        line_array_multi_noun_score = {}

        text_array = re.sub(r"[\w.-]+@[\w.-]+.\w+", "", text_array)
        text_array = re.sub(
            r"(http|ftp|https)://([\w+?\.\w+])+([a-zA-Z0-9\~\!\@\#\$\%\^\&\*\(\)_\-\=\+\\\/\?\.\:\;\'\,]*)?",
            "",
            text_array,
        )

        multi_noun_counter = extract_mecab_multi_noun(text_array, item_counter=item_counter)
        multi_noun_counter_result.update(multi_noun_counter)

    multi_noun_counter_result = upper_char_add_score(multi_noun_counter_result)
    multi_noun_counter_result = check_with_in_text(text, multi_noun_counter_result)

    sorted(multi_noun_counter_result.items(), key=lambda pair: pair[1], reverse=True)
    return multi_noun_counter_result


if __name__ == "__main__":
    input = "act act Act  tes Tes 22\n 22 22 22 \n2222 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 "
    result = extract_multi_noun(input)
    print(result)

    print(check_int_or_float("22"))
