import argparse
import os
import gc
import time

from khaiii import KhaiiiApi

from SmiToText.tokenizer.nltk import nltkSentTokenizer
from SmiToText.util.util import Util

"""
카카오 한글 형태소 분석기를 이용한 명사 추출기

"""

util = Util()
api = KhaiiiApi()


def kakao_postagger_nn_finder(summay_text):
    api.open()
    summary_text_analize = api.analyze(summay_text)
    api.close()

    nn_word_list = []
    for word in summary_text_analize:
        morphs_str = " + ".join([(m.lex + "/" + m.tag) for m in word.morphs])
        # print('-- kakao_postagger --')
        # print(f'{word.lex}\t{morphs_str}')
        # print('-- kakao_postagger --')

        morphs_str_list = morphs_str.split(" + ")

        complex_morphs = ""
        for mophs_item in morphs_str_list:
            if (
                mophs_item.split("/")[1].startswith("N")
                or mophs_item.split("/")[1].startswith("MM")
                or mophs_item.split("/")[1].startswith("SN")
                or mophs_item.split("/")[1].startswith("SL")
            ):
                complex_morphs = complex_morphs + mophs_item.split("/")[0]
        if len(complex_morphs) > 1:
            # print("->", complex_morphs)
            nn_word_list.append(complex_morphs)

        complex_morphs = ""
        if len(morphs_str_list) > 1:
            for mophs_item in morphs_str_list:
                if mophs_item.split("/")[1].startswith("SL") and util.is_alpha(mophs_item.split("/")[0]):
                    complex_morphs = complex_morphs + mophs_item.split("/")[0]
                # elif mophs_item.split("/")[1].startswith("SN") and util.is_int(mophs_item.split("/")[0]) :
                #     complex_morphs = complex_morphs + mophs_item.split("/")[0]

            if len(complex_morphs) > 1:
                # print("->", complex_morphs)
                nn_word_list.append(complex_morphs)
    return nn_word_list


def extract_file_noun(input, output, time_interval=0):
    output_file = open(output, mode="w", encoding="utf-8")
    output_file.close()
    line_number = 1
    input_file = open(input, mode="r", encoding="utf-8")
    while True:
        line = input_file.readline()
        if len(line) < 2:
            break
        line = line.strip()
        line = util.remove_naver_news(line)
        line = util.remove_http_tag(line)
        line = util.normalize(line)

        for line_array in line.split("\n"):
            sentences = nltkSentTokenizer(line_array)

            sentence_words = []
            # for sent in sentences:
            #     sent = sentences.replace('.', ' ')
            #     sent = sentences.replace(',', ' ')
            sent = line_array.replace("  ", " ")
            if len(sent.strip()) == 0:
                continue
            # print('sent:', sent)
            word_list = kakao_postagger_nn_finder(sent)
            # print('word_list:', word_list)
            # eng_word_list = re.findall('[A-Za-z]+', sent)
            # print('eng_word:', eng_word_list)
            # word_list = word_list + eng_word_list
            # print('word+eng_list:', word_list)

            if len(word_list):
                for word in word_list:
                    # if util.check_email(word) or util.is_int(word) or util.is_alpha(word):
                    if util.check_email(word):
                        continue
                    else:
                        if word.startswith(".") or word.startswith(",") or word.startswith("!") or word.startswith("?"):
                            word = word[1:]
                        if word.endswith(".") or word.endswith(",") or word.endswith("!") or word.endswith("?"):
                            word = word[:-1]

                        one_korea_char = [
                            "ㅂ",
                            "ㅈ",
                            "ㄷ",
                            "ㄱ",
                            "ㅅ",
                            "ㅛ",
                            "ㅛ",
                            "ㅕ",
                            "ㅑ",
                            "ㅐ",
                            "ㅔ",
                            "ㅃ",
                            "ㅉ",
                            "ㄸ",
                            "ㄲ",
                            "ㅆ",
                            "ㅒ",
                            "ㅖ",
                            "ㅁ",
                            "ㄴ",
                            "ㅇ",
                            "ㄹ",
                            "ㅎ",
                            "ㅗ",
                            "ㅓ",
                            "ㅏ",
                            "ㅣ",
                            "ㅋ",
                            "ㅌ",
                            "ㅊ",
                            "ㅍ",
                            "ㅠ",
                            "ㅜ",
                            "ㅡ",
                        ]
                        matching = [s for s in one_korea_char if s in word]
                        if len(matching) > 0:
                            # print("-" * 100)
                            # print(len(matching))
                            # print(matching)
                            # print("-" * 100)
                            continue

                        if str(sent).find(word) < 0:
                            continue
                        output_file = open(output, mode="a", encoding="utf-8")
                        output_file.write(word + os.linesep)
                        output_file.close()

                        sentence_words.append(word)
                        # print(line_number, word)
            del word_list

        time.sleep(time_interval)
        print(line_number, sentence_words)

        gc.enable()
        gc.collect()
        line_number += 1

    # while True:
    #     line = input_file.readline()
    #     if line_number < 1000 :
    #         line_number = line_number + 1
    #         continue
    #     if len(line) < 2 or line_number > 2000:
    #         break;
    #     line = line.strip()
    #     line = util.remove_naver_news(line)
    #     line = util.remove_http_tag(line)
    #     line = util.normalize(line)
    #     for line_array in line.split("\n"):
    #         sentences = nltkSentTokenizer(line_array)
    #         sentence_words = []
    #         for sent in sentences:
    #             sent = sent.replace('.', ' ')
    #             sent = sent.replace(',', ' ')
    #             sent = sent.replace('  ', ' ')
    #             if len(sent.strip()) == 0:
    #                 continue
    #             word_list = kakao_postagger_nn_finder(sent)
    #             if len(word_list):
    #                 for word in word_list:
    #                     if util.check_email(word):
    #                         continue
    #                     else:
    #                             word = word[1:]
    #                         if word.endswith(".") or word.endswith(",") or word.endswith("!") or word.endswith("?"):
    #                             word = word[:-1]
    #                         matching = [s for s in one_korea_char if s in word]
    #                         if len(matching) > 0:
    #                             continue
    #                         if str(sent).find(word) < 0:
    #                             continue
    #                         output_file = open(output, mode='a', encoding='utf-8')
    #                         output_file.write(word + os.linesep)
    #                         output_file.close()
    #                         sentence_words.append(word)
    #             del word_list
    #     time.sleep(time_interval)
    #     print('2', line_number, sentence_words)
    #     gc.enable()
    #     gc.collect()
    #     line_number += 1

    input_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract File Noun word")
    parser.add_argument("--input", type=str, required=True, default="", help="Input File")
    parser.add_argument("--output", type=str, required=True, default="", help="Output File")
    parser.add_argument("--interval", type=str, required=False, default="0", help="Time Interval")
    args = parser.parse_args()

    if not args.input:
        print("input file is invalid!")
        exit(1)

    if not args.output:
        print("output file is invalid!")
        exit(1)

    input = str(args.input)
    output = str(args.output)
    time_interval = float(args.interval)

    extract_file_noun(input, output, time_interval)
