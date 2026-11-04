# -*- coding: utf-8 -*-

import re
from SmiToText.util.util import Util
import os


class koLastCharCheck(object):
    def __init__(self):

        self.BASE_CODE, self.CHOSUNG, self.JUNGSUNG = 44032, 588, 28

        self.CHOSUNG_LIST = [
            "ㄱ",
            "ㄲ",
            "ㄴ",
            "ㄷ",
            "ㄸ",
            "ㄹ",
            "ㅁ",
            "ㅂ",
            "ㅃ",
            "ㅅ",
            "ㅆ",
            "ㅇ",
            "ㅈ",
            "ㅉ",
            "ㅊ",
            "ㅋ",
            "ㅌ",
            "ㅍ",
            "ㅎ",
        ]

        self.JUNGSUNG_LIST = [
            "ㅏ",
            "ㅐ",
            "ㅑ",
            "ㅒ",
            "ㅓ",
            "ㅔ",
            "ㅕ",
            "ㅖ",
            "ㅗ",
            "ㅘ",
            "ㅙ",
            "ㅚ",
            "ㅛ",
            "ㅜ",
            "ㅝ",
            "ㅞ",
            "ㅟ",
            "ㅠ",
            "ㅡ",
            "ㅢ",
            "ㅣ",
        ]

        self.JONGSUNG_LIST = [
            " ",
            "ㄱ",
            "ㄲ",
            "ㄳ",
            "ㄴ",
            "ㄵ",
            "ㄶ",
            "ㄷ",
            "ㄹ",
            "ㄺ",
            "ㄻ",
            "ㄼ",
            "ㄽ",
            "ㄾ",
            "ㄿ",
            "ㅀ",
            "ㅁ",
            "ㅂ",
            "ㅄ",
            "ㅅ",
            "ㅆ",
            "ㅇ",
            "ㅈ",
            "ㅊ",
            "ㅋ",
            "ㅌ",
            "ㅍ",
            "ㅎ",
        ]

    def lastKoTextCheck(self, Text):

        split_keyword_list = list(Text)
        # print(split_keyword_list)

        result = list()
        for keyword in split_keyword_list:
            isT = ""
            if re.match(".*[ㄱ-ㅎㅏ-ㅣ가-힣]+.*", keyword) is not None:
                char_code = ord(keyword) - self.BASE_CODE
                char1 = int(char_code / self.CHOSUNG)
                result.append(self.CHOSUNG_LIST[char1])
                # print('초성 : {}'.format(self.CHOSUNG_LIST[char1]))
                char2 = int((char_code - (self.CHOSUNG * char1)) / self.JUNGSUNG)
                result.append(self.JUNGSUNG_LIST[char2])
                # print('중성 : {}'.format(self.JUNGSUNG_LIST[char2]))
                char3 = int((char_code - (self.CHOSUNG * char1) - (self.JUNGSUNG * char2)))
                result.append(self.JONGSUNG_LIST[char3])
                # print('종성 : {}'.format(self.JONGSUNG_LIST[char3]))
                # print('종성 결과:', char3)
                if char3 > 0:
                    isT = 1
                    # print('종성 있음')
                else:
                    isT = 0
                    # print('종성 없음')

        return isT


if __name__ == "__main__":
    KoLastCharCheck = koLastCharCheck()

    util = Util()
    rootDirPath = util.getRootPath("SmiToText.SmiToText")

    print(rootDirPath)
    data_path = rootDirPath + os.path.sep + "data" + os.path.sep + "koDetokenizerData"

    # input_filename = "/home/jjeaby/Dev/06.rosamia/SmiToText/SmiToText/wordcheck/input.txt"
    input_filename = data_path + os.path.sep + "국어_명사_초성포함단어제거.txt"
    output_filename = data_path + os.path.sep + "./국어_명사_초성포함단어제거_mecabUserDict.csv"

    read_file = open(input_filename, mode="r", encoding="utf-8")
    write_file = open(output_filename, mode="w", encoding="utf-8")

    linenum = 0
    while True:
        line = read_file.readline()
        line = line.strip()
        isLastChar = 0
        linenum += 1
        if not line:
            print("NOT LINE : ", "'" + line + "'", linenum)
            break

        isLastChar = KoLastCharCheck.lastKoTextCheck(line)

        if isLastChar == 1:
            print(line + ",,,,NNG,*,T,추가-" + line + ",*,*,*,*")
            write_file.writelines(line + ",,,,NNG,*,T,추가-" + line + ",*,*,*,*" + "\n")
        else:
            print(line + ",,,,NNG,*,F,추가-" + line + ",*,*,*,*")
            write_file.writelines(line + ",,,,NNG,*,F,추가-" + line + ",*,*,*,*" + "\n")

        isLastChar = 0

    write_file.close()
    read_file.close()
