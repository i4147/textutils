import re
import math
import time
import spacy

from emoji import unicode_codes
from prettytable import PrettyTable
import argparse
import json


class TextStats:
    def __init__(self) -> None:
        self._lineCount = 0
        self._wordCount = 0
        self._emailCount = 0
        self._urlCount = 0
        self._emojiCount = 0
        self._emojiLines = 0
        self._impunCount = 0
        self._punCount = 0
        self._avgWordsPerLine = 0
        self._percentEmoji = 0
        self._percentEmail = 0
        self._percentUrl = 0
        self._percentImpoperPunc = 0
        self._percentPunc = 0
        self._totalEmojis = 0
        self._start = time.time()

        self._wordsPerLine = []
        self._emojiGroupCount = []
        self._wordRange = {}
        self._sortedRange = {}
        self._dictNer = {}
        self._jsonObj = {}

        self.__properPunctuations = (".", ",", "!", "?")
        self.__improperPunctuations = (":", ";", "-", "()", "\{\}", "[]", '"', "'", "...")
        self.__email_pattern = r"[a-zA-Z][a-zA-Z0-9\.]{2,256}@[a-zA-Z0-9]{2,256}\.[a-z]{2,10}(\.[a-z]{2,3})?"
        self.__url_pattern_modify = (
            r"((http|https)://)?(www\.)?[a-zA-Z0-9]{2,256}\.(com|edu|gov|co|org|net)(\.[a-z]{2,3})?"
        )
        self.__emoji_pattern = r"U\+1F\w{2,4}"

        self.__nlp = spacy.load("en_core_web_sm")

    def storeNer(self, key):
        if key not in self._dictNer:
            self._dictNer[key] = 1

        else:
            self._dictNer[key] += 1

    def spacy_enty(self, sentence):
        doc = self.__nlp(sentence)
        for ent in doc.ents:
            self.storeNer(ent.label_)

    def getPercentNer(self, value):
        #  for key, value in self._dictNer.items():
        #   print(key, " : ", value, " ", f"({(round(((value/self._wordCount) * 100), 2))}%)")
        return f"({(round(((value / self._wordCount) * 100), 2))}%)"

    def getEmailCount(self, line):
        email = re.findall(self.__email_pattern, line)
        return len(email)

    def getUrlCount(self, line):
        url = re.findall(self.__url_pattern_modify, line)
        return len(url)

    def getWordCount(self, line):
        words = line.split(" ")
        return (len(words), words)

    def updateRange(self, words):
        minRange = len(words) - (len(words) % 10)
        key = f"{minRange}-{minRange + 10}"

        if key in self._wordRange.keys():
            self._wordRange[key] += 1

        else:
            self._wordRange[key] = 1

    def sortedWordRange(self):
        sortRange = sorted(self._wordRange.items(), key=lambda x: int(x[0].split("-")[0]))
        self._sortedRange = dict(sortRange)

    def countImpPunctuations(self, line):
        return line.rstrip().endswith(self.__improperPunctuations)

    def countPunctuations(self, line):
        return line.rstrip().endswith(self.__properPunctuations)

    def getEmojiCount(self, words):
        for txt in words:
            emojiFormat = map(lambda x: "U+{:X}".format(ord(x)), txt)
            for emojiStr in emojiFormat:
                emojiLineCheck = len(re.findall(self.__emoji_pattern, emojiStr))
                if emojiLineCheck > 0:
                    return 1

        return 0

    def getEmojiCountEff(self, words):
        emojis = 0
        for txt in words:
            groupCount = 0
            for chars in txt:
                if chars in unicode_codes.EMOJI_DATA:
                    emojis = 1
                    groupCount += 1

            if groupCount > 1:
                self._emojiGroupCount.append(groupCount)

            self._totalEmojis += groupCount
        return emojis

    def getAvgWords(self):
        return math.ceil(self._wordCount / self._lineCount)

    def getPercentEmoji(self):
        return round(
            (
                (self._emojiCount - len(self._emojiGroupCount) + sum(self._emojiGroupCount))
                / (self._wordCount - len(self._emojiGroupCount) + sum(self._emojiGroupCount))
            )
            * 100,
            2,
        )

    def getPercentEmail(self):
        return round((self._emailCount / self._wordCount) * 100, 2)

    def getPercentUrl(self):
        return round((self._urlCount / self._wordCount) * 100, 2)

    def getPercentImproperPunc(self):
        return round((self._impunCount / self._lineCount) * 100, 2)

    def getPercentproperPunc(self):
        return round((self._punCount / self._lineCount) * 100, 2)

    def convertJsonObj(self, keys, values):
        jsonObj = self._jsonObj

        for key, value in zip(keys, values):
            jsonObj[key] = int(value.split(" ")[0])

        for key, value in self._dictNer.items():
            jsonObj[key.lower()] = value

        jsonObj["wordPerLine"] = dict(self._sortedRange.items())
        return json.dumps(jsonObj, indent=2)

    def displayResult(self):
        values = [
            f"{self._wordCount}",
            f"{self._lineCount}",
            f"{self._avgWordsPerLine}",
            f"{self._totalEmojis} ({self._percentEmoji}%)",
            f"{self._emailCount} ({self._percentEmail}%)",
            f"{self._urlCount} ({self._percentUrl}%)",
            f"{self._punCount} ({self._percentPunc}%)",
            f"{self._impunCount} ({self._percentImpoperPunc}%)",
        ]

        SpacyLabelKeys = [label for label in self._dictNer.keys()]
        SpacyLabelValues = [f"{value}\n{self.getPercentNer(value)}" for value in self._dictNer.values()]
        keys = ["Words", "Lines", "avgWordPerLine", "emojis", "emails", "urls", "properPunct", "improperPunct"]
        table1 = PrettyTable(keys)
        table1.add_row(values)
        table2 = PrettyTable(["Words/Line(Range)", "Lines in Given Range"])

        labelTable = PrettyTable(SpacyLabelKeys)
        labelTable.add_row(SpacyLabelValues)

        for key, value in self._sortedRange.items():
            table2.add_row([key, value])

        # print("\n", table1)
        # print("\n", labelTable)
        # print("\n", table2)

        jsonObj = self.convertJsonObj(keys, values)
        return jsonObj

    def displayOption(self, options):
        values = []
        for opt in options:
            values.append(eval("self._" + opt))

        table1 = PrettyTable(options)
        table1.add_row(values)

        # print("\n", table1)

        for key, value in zip(options, values):
            self._jsonObj[key] = value

        return json.dumps(self._jsonObj, indent=2)

    def main(self, filename):

        with open(filename, "r") as file:
            print(f"\n\n\t\t File || {str(filename).split('/')[-1]} || is Processing.... \n\n")
            line = file.readline()

            print("Collecting resources...")
            while line:
                self._lineCount += 1

                if self._lineCount == 1000:
                    print("Please be Patient... Large Files might take some time to load!")
                self.spacy_enty(line)

                self._emailCount += self.getEmailCount(line)
                self._urlCount += self.getUrlCount(line)
                wordsCnt, words = self.getWordCount(line)
                self._wordCount += wordsCnt
                self.updateRange(words)
                self.sortedWordRange()
                self._impunCount += self.countImpPunctuations(line)
                self._punCount += self.countPunctuations(line)
                # self._emojiCount += self.getEmojiCount(words)
                self._emojiCount += self.getEmojiCountEff(words)

                line = file.readline()
        self._avgWordsPerLine = self.getAvgWords()
        self._percentUrl = self.getPercentUrl()
        self._percentEmail = self.getPercentEmail()
        self._percentEmoji = self.getPercentEmoji()
        self._percentPunc = self.getPercentproperPunc()
        self._percentImpoperPunc = self.getPercentImproperPunc()

        def __del__(self):
            del self


def getFiles():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", "--words", help="To get the word Count", dest="wordCount", required=False, action="store_true"
    )
    parser.add_argument(
        "-l", "--lines", help="To get the word Count", dest="lineCount", required=False, action="store_true"
    )
    parser.add_argument(
        "-em", "--emojis", help="To get the word Count", dest="emojiCount", required=False, action="store_true"
    )
    parser.add_argument(
        "-u", "--urls", help="To get the word Count", dest="urlCount", required=False, action="store_true"
    )
    parser.add_argument(
        "-e", "--emails", help="To get the word Count", dest="emailCount", required=False, action="store_true"
    )
    parser.add_argument(
        "-av", "--avg", help="To get the word Count", dest="avgWordsPerLine", required=False, action="store_true"
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Enter space seprated filename for as many files you want to open",
        dest="filename",
        required=True,
        nargs="+",
    )

    args = parser.parse_args()
    return args


def runFile():
    args = getFiles()
    fileArray = args.filename

    options = []
    if args.wordCount:
        options.append("wordCount")
    if args.lineCount:
        options.append("lineCount")
    if args.emojiCount:
        options.append("emojiCount")
    if args.urlCount:
        options.append("urlCount")
    if args.emailCount:
        options.append("emailCount")
    if args.avgWordsPerLine:
        options.append("avgWordsPerLine")

    for files in fileArray:
        try:
            textStats = TextStats()
            textStats.main(files)
            if len(options) < 1:
                getJsonObj = textStats.displayResult()

            else:
                getJsonObj = textStats.displayOption(options)

            print("\nStatus - Completed Successfully. :)")
            return getJsonObj

        except Exception as e:
            print("\n---------------------------------------------------------------------------------------------")
            print(f"OOPS! Could not find your file!")
            print(f"Check Whether Your file exists with name ('{str(files).split('/')[-1]}')")
            print("\nStatus - Not Found. :(")
            print("---------------------------------------------------------------------------------------------")
            continue


if __name__ == "__main__":
    begin = time.time()

    runFile()

    end = time.time()
    print(end - begin)
