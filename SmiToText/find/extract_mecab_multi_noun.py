import argparse
import copy
import itertools
import os
import re
from datetime import date
import json

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
    cleaning_multi_noun_result = []
    cleaning_multi_noun_result_score = {}

    for multi_noun in multi_noun_list:
        multi_noun = re.sub(r"[\s]+", " ", multi_noun)
        isOnlyEngNum = re.sub("[a-zA-Z0-9]", "", multi_noun)

        if len(isOnlyEngNum.strip()) == 0:
            multi_noun = re.sub(r"[\s]+", " ", multi_noun)
            cleaning_multi_noun_result.append(multi_noun)
            if len(multi_noun_list_score) == 0:
                if not in_dict(cleaning_multi_noun_result_score, multi_noun):
                    check_capitalize_score = (
                        1000 * len(re.findall("[A-Z]+", multi_noun)) / len(multi_noun.replace(" ", ""))
                    )
                    cleaning_multi_noun_result_score[multi_noun] = 0.75 + check_capitalize_score
                else:
                    cleaning_multi_noun_result_score[multi_noun] += 0.75
                continue
            else:
                if in_dict(cleaning_multi_noun_result_score, multi_noun) == False:
                    cleaning_multi_noun_result_score[multi_noun] = multi_noun_list_score[multi_noun]
                else:
                    cleaning_multi_noun_result_score[multi_noun] += multi_noun_list_score[multi_noun]
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
                    cleaning_multi_noun_result.append(candidate_multi_noun)

                    if len(multi_noun_list_score) == 0:
                        if not in_dict(cleaning_multi_noun_result_score, candidate_multi_noun):
                            check_capitalize_score = (
                                1000
                                * len(re.findall("[A-Z]+", candidate_multi_noun))
                                / len(candidate_multi_noun.replace(" ", ""))
                            )
                            cleaning_multi_noun_result_score[candidate_multi_noun] = 0.75 + check_capitalize_score
                        else:
                            cleaning_multi_noun_result_score[candidate_multi_noun] += 0.75
                    else:
                        if not in_dict(cleaning_multi_noun_result_score, candidate_multi_noun):
                            cleaning_multi_noun_result_score[candidate_multi_noun] = multi_noun_list_score[
                                candidate_multi_noun
                            ]
                        else:
                            cleaning_multi_noun_result_score[candidate_multi_noun] += multi_noun_list_score[
                                candidate_multi_noun
                            ]
                else:
                    if not in_dict(cleaning_multi_noun_result_score, candidate_multi_noun):
                        check_capitalize_score = (
                            1000
                            * len(re.findall("[A-Z]+", candidate_multi_noun))
                            / len(candidate_multi_noun.replace(" ", ""))
                        )
                        cleaning_multi_noun_result_score[candidate_multi_noun] = 0.75 + check_capitalize_score
                    else:
                        cleaning_multi_noun_result_score[candidate_multi_noun] += 0.75

    return sorted_dict(cleaning_multi_noun_result_score)


def krwordrank_noun(sentence_list=[], min_count=5, max_length=10, beta=0.85, max_iter=10, verbose=False):
    krword_rank_noun = []
    krword_rank_noun_score = {}

    wordrank_extractor = KRWordRank(min_count, max_length, verbose)
    try:
        keywords, rank, graph = wordrank_extractor.extract(sentence_list, beta, max_iter)
        for word, r in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[: len(keywords)]:
            word = re.sub(r"[\s]+", " ", word)
            if len(word) > 1:
                word_cleansing = re.sub("[-=+,#/\\?:^$.@*\"※~&%ㆍ!”』\\‘|\\(\\)\\[\\]\\<\\>`'…》\\^\\)\\(▶]", "", word)
                if len(word_cleansing) == len(word):
                    krword_rank_noun.append(word)
                    krword_rank_noun_score[word] = r
        return sorted_dict(krword_rank_noun_score)
    except:
        krword_rank_noun = []
        krword_rank_noun_score = {}
        return sorted_dict(krword_rank_noun_score)


def remove_stopword(multi_noun, multi_noun_score, stop_word=[]):
    if len(stop_word) == 0 or stop_word == None:
        stop_word = all_stop_word

    check_multi_noun = []
    check_multi_noun_score = {}

    for noun in multi_noun:
        if (
            noun not in stop_word
            and not Util().is_int(noun)
            and not str(noun).endswith("니다")
            and not str(noun).endswith("이다")
        ):
            check_multi_noun.append(noun)
            check_multi_noun_score[noun] = multi_noun_score[noun]

    return sorted_dict(check_multi_noun_score)


def check_stopword(multi_noun, multi_noun_score, stop_word=[]):
    if len(stop_word) == 0 or stop_word == None:
        stop_word = all_stop_word
    check_multi_noun = []
    check_multi_noun_score = {}

    for noun in multi_noun:
        if (
            len(set(stop_word).difference(noun.split())) == len(stop_word)
            and len(set(stop_word).difference([noun.replace(" ", "")])) == len(stop_word)
            and not Util().is_int(noun)
            and not str(noun).endswith("니다")
            and not str(noun).endswith("이다")
        ):
            check_multi_noun.append(noun)
            check_multi_noun_score[noun] = multi_noun_score[noun]

    return sorted_dict(check_multi_noun_score)


def remove_last_one_char(multi_noun, multi_noun_score):
    check_multi_noun = []
    check_multi_noun_score = {}

    for noun in multi_noun:
        temp_noun = noun.split(" ")
        if len(temp_noun[0]) == 1:
            check_multi_noun.append(" ".join(temp_noun[1:]))
            check_multi_noun_score[str(" ".join(temp_noun[1:]))] = multi_noun_score[noun]
        elif len(temp_noun[-1]) == 1:
            check_multi_noun.append(" ".join(temp_noun[:-1]))
            check_multi_noun_score[str(" ".join(temp_noun[:-1]))] = multi_noun_score[noun]
        else:
            check_multi_noun.append(noun)
            check_multi_noun_score[noun] = multi_noun_score[noun]

    return sorted_dict(check_multi_noun_score)


def sorted_dict(multi_noun_score):
    ret_check_multi_noun = []
    ret_check_multi_noun_score = {}
    for noun, r in sorted(multi_noun_score.items(), key=lambda x: x[1], reverse=True)[: len(multi_noun_score)]:
        if r > 0:
            ret_check_multi_noun.append(noun)
            ret_check_multi_noun_score[noun] = r

    return ret_check_multi_noun, ret_check_multi_noun_score


def multi_noun_score_add(multi_noun_score, krword_rank_once_noun_score):
    tem_add_noun_score = {}
    for multi_noun in multi_noun_score.keys():
        temp_multi_noun = re.sub(r"[\s]+", " ", multi_noun)
        for krword_noun in krword_rank_once_noun_score.keys():
            temp_krword_noun = re.sub(r"[\s]+", " ", krword_noun)

            if len(temp_multi_noun) > len(temp_krword_noun):
                temp_multi_noun_eng_check = re.sub("[ㄱ-힗]", "", temp_multi_noun)
                if temp_multi_noun_eng_check.strip().lower() == temp_krword_noun.strip().lower():
                    tem_add_noun_score[krword_noun] = (
                        krword_rank_once_noun_score[krword_noun] + multi_noun_score[multi_noun]
                    )
                    multi_noun_score[multi_noun] = 0
                elif len(temp_multi_noun.replace(temp_krword_noun, "")) < len(temp_multi_noun):
                    multi_noun_score[multi_noun] += krword_rank_once_noun_score[krword_noun]
                else:
                    check_capitalize_score = (
                        1000 * len(re.findall("[A-Z]+", krword_noun)) / len(krword_noun.replace(" ", ""))
                    )
                    tem_add_noun_score[krword_noun] = 0.75 + check_capitalize_score

            else:
                if len(temp_krword_noun.replace(temp_multi_noun, "")) < len(temp_krword_noun):
                    multi_noun_score[multi_noun] += krword_rank_once_noun_score[krword_noun]
                else:
                    check_capitalize_score = (
                        1000 * len(re.findall("[A-Z]+", krword_noun)) / len(krword_noun.replace(" ", ""))
                    )
                    tem_add_noun_score[krword_noun] = 0.75 + check_capitalize_score

    multi_noun_score.update(tem_add_noun_score)

    temp_krword_noun, _ = sorted_dict(multi_noun_score)
    if len(temp_krword_noun) == 0:
        return sorted_dict(krword_rank_once_noun_score)
    else:
        return sorted_dict(multi_noun_score)


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


def extract_mecab_multi_noun(text, item_counter=0):
    text = text.strip()

    multi_noun = []
    multi_noun_score = {}
    krword_rank_noun = []
    krword_rank_noun_score = {}
    krword_rank_once_noun = []
    krword_rank_once_noun_score = {}

    if text:
        sentence_list = nltkSentTokenizer(text)

        for sentence in sentence_list:
            sentence = sentence.strip()
            if sentence:
                first_multi_noun_list, _ = expect_multi_noun_text_ko(sentence)
                first_single_noun_list, _ = expect_single_noun_text_ko(sentence)

                first_multi_noun_list.extend(first_single_noun_list)

                second_multi_noun_list, second_multi_noun_list_score = cleaning_multi_noun(
                    first_multi_noun_list, cleaning_count=2
                )

                multi_noun.extend(second_multi_noun_list)
                multi_noun_score.update(second_multi_noun_list_score)

        krword_rank_noun, krword_rank_noun_score = krwordrank_noun(sentence_list=sentence_list, min_count=5)
        krword_rank_once_noun, krword_rank_once_noun_score = krwordrank_noun(sentence_list=sentence_list, min_count=2)

    multi_noun.extend(krword_rank_noun)
    multi_noun_score.update(krword_rank_noun_score)

    multi_noun, multi_noun_score = check_stopword(multi_noun, multi_noun_score)

    krword_rank_once_noun, krword_rank_once_noun_score = check_stopword(
        krword_rank_once_noun, krword_rank_once_noun_score
    )

    multi_noun, multi_noun_score = remove_last_one_char(multi_noun, multi_noun_score)

    multi_noun, multi_noun_score = check_stopword(multi_noun, multi_noun_score)

    multi_noun, multi_noun_score = multi_noun_score_add(multi_noun_score, krword_rank_once_noun_score)

    multi_noun, multi_noun_score = remove_stopword(multi_noun, multi_noun_score)

    return_multi_noun, return_multi_noun_score = text_in_mult_noun_finder(multi_noun, multi_noun_score, text)

    if item_counter == 0:
        return return_multi_noun, return_multi_noun_score
    else:
        return return_multi_noun[:item_counter], dict(itertools.islice(return_multi_noun_score.items(), item_counter))


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

    for text_array in text.split("\n"):
        text_array = text_array.strip()

        line_array_multi_noun_score = {}

        text_array = re.sub(r"[\w.-]+@[\w.-]+.\w+", "", text_array)
        text_array = re.sub(
            r"(http|ftp|https)://([\w+?\.\w+])+([a-zA-Z0-9\~\!\@\#\$\%\^\&\*\(\)_\-\=\+\\\/\?\.\:\;\'\,]*)?",
            "",
            text_array,
        )

        multi_noun_list, multi_noun_list_score = extract_mecab_multi_noun(text_array, item_counter=item_counter)

        if len(multi_noun_list):
            for index, word in enumerate(multi_noun_list):
                if Util().check_email(word):
                    continue
                else:
                    add_flag = True
                    for char in word:
                        if char in [
                            "'",
                            "`",
                            ",",
                            "'",
                            '"',
                            "|",
                            "!",
                            "@",
                            "#",
                            "$",
                            "%",
                            "^",
                            "&",
                            "*",
                            "(",
                            ")",
                            "“",
                            "-",
                            "_",
                            "=",
                            "+",
                            "<",
                            ">",
                            ".",
                            ";",
                            ":",
                            "ㄱ",
                            "ㄴ",
                            "ㄲ",
                            "ㅂ",
                            "ㅃ",
                            "ㅈ",
                            "ㅉ",
                            "ㄷ",
                            "ㄸ",
                            "ㄱ",
                            "ㅁ",
                            "ㅇ",
                            "ㄹ",
                            "ㅎ",
                            "ㅅ",
                            "ㅆ",
                            "ㅍ",
                            "ㅊ",
                            "ㅌ",
                            "ㅋ",
                            "ㅛ",
                            "ㅕ",
                            "ㅑ",
                            "ㅐ",
                            "ㅔ",
                            "ㅗ",
                            "ㅓ",
                            "ㅏ",
                            "ㅣ",
                            "ㅠ",
                            "ㅜ",
                            "ㅡ",
                            " ",
                        ]:
                            add_flag = False

                    if (
                        word == "기자"
                        or word == str(date.today().day) + "일"
                        or word.strip() == ""
                        or len(word.strip()) == 1
                    ):
                        add_flag = False

                    if check_en_stopword(word):
                        add_flag = False

                    if add_flag:
                        word_score = {word: multi_noun_list_score[word]}
                        line_array_multi_noun_score.update(word_score)

    return sorted_dict(line_array_multi_noun_score)


if __name__ == "__main__":
    _, a = extract_multi_noun(
        '[6·17 대책]3억 넘는 집사면 전세대출 회수…법인 주담대는 \'금지\'(종합) ∥ \n \n \n\n\n\n// flash 오류를 우회하기 위한 함수 추가\nfunction _flash_removeCallback() {}\n\n \n "주택구입시 전입·처분 요건 강화"\r"보금자리론 대출자, 실거주 유지 의무"\r"HUG 전세대출보증한도 2억으로 낮춰"[서울=뉴시스]김명원 기자 = 김현미 국토교통부 장관이 17일 오전 서울 종로구 정부서울청사 합동브리핑실에서 갭투자 규제를 핵심 내용으로 한 문재인 정부 21번째 부동산대책을 발표하고 있다. 2020.06.17. kmx1105@newsis.com[서울=뉴시스] 정옥주 기자 = 정부가 갭투자(전세 낀 주택 매입) 차단을 위해 주택담보대출 요건과 전세자금대출보증 이용 제한을 강화하기로 했다. 또 법인을 활용한 투기 수요 근절을 위해 주택 매매·임대사업자의 주택담보대출을 전면 금지키로 했다.기획재정부와 국토교통부, 금융위원회 등 정부부처는 17일 정부서울청사에서 \'주택시장 안정을 위한 관리방안\' 브리핑을 열고 이 같은 방안을 발표했다.이에 따르면 정부는 투기지역·투기과열지구 내 시가 3억원 초과 아파트를 신규 구입하는 경우도 전세대출 보증 제한 대상에 추가하기로 했다. 전세대출을 받은 후 투기지역·투기과열지구 내 3억원 초과 아파트를 구입하는 경우 전세대출을 즉시 회수한다.종전에는 시가 9억원 초과 주택 보유자에 대해 전세대출 보증을 제한하고, 전세대출을 받은 후 9억원 초과 주택을 구입하면 대출을 즉시 회수했다.하지만 보증금을 승계해 매수하는 갭 투자 비중이 계속해서 증가 추세를 보이자, 이를 차단하고 실수요를 보호하기 위해 주담대 실수요 요건과 전세자금대출 규제 강화라는 카드를 꺼내들었다. 실제로 서울 지역의 갭 투자 비중은 올해 1월 48.4%에서 지난 5월 52.4%로 높아졌다. 특히 강남 4구의 경우 같은 기간 57.5%에서 72.7%로 뛰어올랐다.다만 12·16 대책 등 기존 규제사례에서 인정된 불가피한 실수요 등에 대해서는 예외를 인정키로 했다. ▲직장 이동·자녀 교육·부모 봉양 등 실수요 목적 ▲시·군간 이동할 경우 ▲전셋집과 구입주택 모두에서 전세로 실거주할 경우 등이다.규제지역 내 주택 구입을 위해 주담대를 받는 경우 전입과 처분 요건도 강화했다.현재는 무주택자가 투기지역·투기과열지구 내 시가 9억원 초과 주택 구입을 위해 주담대를 받으면, 1년내 전입(조정대상지역은 2년) 의무를 부과하고 있다. 그러나 앞으로는 전 규제지역 내 주택 구입을 위해 주담대를 받는 경우 주택가격과 관계없이 6개월내 전입 의무가 부과된다. 1주택자들은 전 규제지역 내 주택구입을 위해 주담대를 받는 경우 6개월내 기존주택을 처분하고, 신규주택 전입해야 한다.전산개발 및 준비 등을 감안해 오는 7월1일부터 시행된다. 다만 행정지도 시행 전 주택매매계약을 체결하고 계약금을 이미 납부한 사실을 증명한 차주, 대출 신청접수를 완료한 차주 등에 대해서는 종전 규정을 적용한다.단 가계약의 경우 종전 규정이 적용되지 않는다.6개월 산정시점은 주택담보대출 실행일부터다. 단 중도금·이주비 대출의 경우 신규 주택 소유권 이전 등기일로부터 6개월이다.만약 전입하지 않으면 기한의 이익이 상실돼 대출을 상환해야 하며, 차주는 향후 3년간 주택관련 대출을 받는 것이 제한된다.보금자리론 대출자들에는 실거주 유지 의무가 부과된다. 지금은 보금자리론 이용 차주에게 전입 의무는 부과되지 않고 있다. 그러나 주택금융공사 내규 개정 시행일인 다음달 1일 이후 보금자리론 신청 분부터 3개월 내 전입 및 1년 이상 실거주 유지 의무가 부과된다. 이를 위반하면 대출금이 회수된다.보금자리론 대출자는 대출실행 시점 또는 대출 실행 후 3개월 내에 전입 후 \'전입세대열람원\'을 은행에 제출해야 한다. 주택금융공사는 대출실행 후 일정 기간이 지나면 전입 여부를 조사할 수 있으며, 약정을 위반해 전출한 게 확인된 경우 기한이익 상실 조치를 한다.주택도시보증공사(HUG)의 전세대출 보증한도는 2억원으로 축소된다. 현재 수도권 4억원, 지방 3억2000만원인 HUG의 전세대출 보증한도를 1주택자에 한해 주택금융공사 수준인 2억원으로 낮춘다. 이는 현재 전세대출 보증한도가 보증기관별로 차이가 있어 1주택자의 갭 투자 용도로 활용되고 있다는 지적에 따른 것이다. HUG 내규 개정 시행일 이후 전세대출 신규 신청분부터 적용될 예정이다.이세훈 금융위 금융정책국장은 "전세대출 규제는 주금공과 HUG 등 공적보증에 대해 적용되며 SGI서울보증에도 협조를 요청할 예정"이라고 말했다.부동산 법인의 투기수요를 막기 위해 주택 매매·임대사업자의 주담대는 전면 금지키로 했다.이는 건물과 토지 등 부동산을 구입한 후 재판매하거나 임대하는 부동산 매매업·임대업 법인이 빠르게 증가하는 것에 대응하기 위한 조치다. 법인이 아파트를 매수한 비중은 지난 2017년 1%에서 지난해 3%로 증가했으며, 특히 인천·청주 등 시장 과열지역에서 매수비중이 큰 폭으로 늘었다.이에 따라 다음달 1일부터 모든 지역 주택 매매·임대사업자에 대한 주담대가 금지된다. 기존에는 규제지역 내 주택 매매·임대사업자의 주담대는 LTV(담보인정비율) 20%~50%를 적용했고, 비규제지역은 규제가 없었다.시설자금뿐 아니라 운전자금용으로도 주담대를 받을 수 없다. 단 임차인 보호를 위해 주택 매매·임대사업자가 올해 7월1일 전까지 취득한 주택을 담보로 하는 임차보증금 반환 목적 대출은 허용하기로 했다.이 국장은 "이번 대책은 법인거래와 갭투자가 시장불안 요인으로 작용하고 있다는 점에 주목했다"며 "실거주를 강화한 것으로, 거래관행으로 볼 때 이사가는 집을 정해놓고 매매하기 때문에 실수요를 과도하게 제한하는 것은 아니라고 판단된다"고 말했다.☞공감언론 뉴시스channa224@newsis.com▶ 네이버에서 뉴시스 구독하기▶ K-Artprice, 유명 미술작품 가격 공개▶ 뉴시스 빅데이터 MSI 주가시세표 바로가기<ⓒ 공감언론 뉴시스통신사. 무단전재-재배포 금지>\n \n'
    )

    print(a)
