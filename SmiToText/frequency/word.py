from collections import Counter

from langdetect import detect

from SmiToText.tokenizer import mecab
from SmiToText.tokenizer import nltk


def word_tags(text):
    count = Counter([text.strip()])
    return count


def nltk_word_tags(text):
    nltkSentence = nltk.nltkTokenizer(text)
    nltkSentence = nltkSentence.split(" ")
    nltkSentence = [n for n in nltkSentence if len(n) > 0]
    count = Counter(nltkSentence)
    return count


def mecab_word_tags(text):
    mecabSentence = mecab.mecabTokenizer(text)
    mecabSentence = mecabSentence.split(" ")
    mecabSentence = [n for n in mecabSentence if len(n) > 0]
    count = Counter(mecabSentence)
    return count


def word_rank_list(countText):

    return_list = []
    for n, c in countText.most_common():
        temp = {"tag": n, "count": c}
        return_list.append(temp)
    return return_list


def word_tag_count(text, auto_lang_check=True):
    if auto_lang_check == True:
        try:
            lang = detect(text)

            if lang == "en" or lang == "no":
                word_count = nltk_word_tags(text)
            elif lang == "ko":
                word_count = mecab_word_tags(text)
            else:
                word_count = nltk_word_tags(text)
        except:
            word_count = nltk_word_tags(text)
    else:
        word_count = nltk_word_tags(text)

    return word_count


if __name__ == "__main__":
    while True:
        try:
            inputText = input("\n\n문장을 입력하세요?: \n")
        except UnicodeDecodeError:
            print("다시 입력하세요\n")
            continue

        if inputText == "exit":
            exit(1)

        countText = mecab_word_tags(inputText)
        print(countText)
        print(word_rank_list(countText))
