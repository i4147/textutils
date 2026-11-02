from nltk.tokenize import word_tokenize
import random
import os
import pandas as pd
import hashlib
from . import Global


class Operation(object):
    def __init__(self, probability) -> None:
        self.probability = probability

    def perform_operation(self, text):
        raise RuntimeError("Illegal call to abstract base class function. Exiting.")

    def __str__(self) -> str:
        return self.__class__.__name__


class SwapWords(Operation):
    def __init__(self, probability):
        Operation.__init__(self, probability)

    def perform_operation(self, text):
        words = word_tokenize(text)
        usable_words = [word for word in words if word.isalpha()]
        if len(usable_words) < 2:
            return text
        r_word_1 = random.randint(0, len(usable_words) - 1)
        if r_word_1 == len(usable_words) - 1:
            r_word_2 = r_word_1 - 1
        else:
            r_word_2 = r_word_1 + 1
        return text.replace(
            usable_words[r_word_1] + " " + usable_words[r_word_2],
            usable_words[r_word_2] + " " + usable_words[r_word_1],
            1,
        )


class SwapCharacters(Operation):
    def __init__(self, probability):
        Operation.__init__(self, probability)
        self.probability = probability

    def perform_operation(self, text):
        words = word_tokenize(text)
        usable_words = [word for word in words if word.isalpha() and len(word) >= 2]
        if len(usable_words) <= 1:
            return text
        random_word_index = random.randint(0, len(usable_words) - 1)
        word = usable_words[random_word_index]
        chars = list(word)
        random_char_index = random.randint(0, len(chars) - 1)
        if random_char_index == len(chars) - 1:
            random_char_index_neighbour = random_char_index - 1
        else:
            random_char_index_neighbour = random_char_index + 1
        chars[random_char_index], chars[random_char_index_neighbour] = (
            chars[random_char_index_neighbour],
            chars[random_char_index],
        )
        new_word = "".join(chars)
        return text.replace(usable_words[random_word_index], new_word, 1)


class Misspeller(Operation):
    def __init__(self, probability, aggressive):
        Operation.__init__(self, probability)
        self.aggressive = aggressive

    def perform_operation(self, text):
        words = word_tokenize(text)
        usable_words = [word for word in words if word.isalpha()]
        r_word = random.choice(usable_words)
        r_word_chars = list(r_word)
        r_char_index = random.randint(0, len(r_word_chars) - 1)
        r_word_chars[r_char_index] = random.choice(
            get_neighbouring_character(r_word_chars[r_char_index], aggressive=self.aggressive)
        )
        new_word = "".join(r_word_chars)
        return text.replace(r_word, new_word, 1)


class ReplaceNumbers(Operation):
    def __init__(self, probability, replace_all=False):
        Operation.__init__(self, probability)

    def perform_operation(self, text):
        words = word_tokenize(text)
        numbers = [word for word in words if word.isdecimal() and 0 <= int(word) <= 99]
        if len(numbers) != 0:
            to_replace = random.choice(numbers)
            return text.replace(to_replace, ZERO_TO_ONE_HUNDRED_NUMERIC[int(to_replace)])
        else:
            return text


class ReplaceWordsWithNumbers(Operation):
    def __init__(self, probability):
        Operation.__init__(self, probability)

    def perform_operation(self, text):
        words = word_tokenize(text)
        list_of_written_numbers = []
        for word in words:
            if word in ZERO_TO_ONE_HUNDRED_TEXT:
                list_of_written_numbers.append(word)
        if len(list_of_written_numbers) != 0:
            to_replace = random.choice(list_of_written_numbers)
            return text.replace(to_replace, ZERO_TO_ONE_HUNDRED_TEXT[to_replace])
        else:
            return text


class RxNorm(Operation):
    def __init__(self, probability, icd_file="icd102019-covid-expandedsyst_codes.txt"):
        Operation.__init__(self, probability)
        names = [
            "RXCUI",
            "LAT",
            "TS",
            "LUI",
            "STT",
            "SUI",
            "ISPREF",
            "RXAUI",
            "SAUI",
            "SCUI",
            "SDUI",
            "SAB",
            "TTY",
            "CODE",
            "STR",
            "SRL",
            "SUPPRESS",
            "CVF",
        ]
        RXNCONSO = pd.read_csv("/home/mblo/.augmentext/rxnorm/rrf/RXNCONSO.RRF", sep="|", header=None, names=names)

    def perform_operation(self, text):
        pass


class PhoneticMisspeller(Operation):
    pass


class ICDFromText(Operation):
    def __init__(self, probability, icd_file="icd102019-covid-expandedsyst_codes.txt"):
        Operation.__init__(self, probability)
        if Global.ICD is not None:
            print(len(Global.ICD))
        else:
            print("ICD not yet defined...")

    def perform_operation(self, text):
        pass


class ICDToText(Operation):
    def __init__(self, probability, icd_file="icd102019-covid-expandedsyst_codes.txt"):
        Operation.__init__(self, probability)
        if not Global.ICD.ready:
            userhome = os.path.expanduser("~")
            augmentext_home = os.path.join(userhome, ".augmentext")
            if not os.path.exists(augmentext_home):
                os.mkdir(augmentext_home)
            icd_home = os.path.join(augmentext_home, "icd")
            if not os.path.exists(icd_home):
                os.mkdir(icd_home)
            icd_full_path = os.path.join(icd_home, icd_file)
            headers = [
                "Level",
                "PlaceNT",
                "NodeTypeXS",
                "ChapterNumber",
                "CodeThreeChars",
                "CodeWithoutDagger",
                "CodeWithoutAsterisk",
                "CodeWithoutDot",
                "Title",
                "Chapter",
                "TitleAlt",
                "Empty",
                "Mortality1",
                "Mortality2",
                "Mortality3",
                "Mortality4",
                "Morbidity",
            ]
            if os.path.isfile(icd_full_path):
                md5_calculated = hashlib.md5(open(icd_full_path, "rb").read()).hexdigest()
                assert md5_calculated == Global.ICD.md5
                Global.ICD.df = pd.read_csv(icd_full_path, sep=";", header=None, names=headers)
                Global.ICD.code_dict = pd.Series(
                    Global.ICD.df.Title.values, index=Global.ICD.df.CodeWithoutAsterisk
                ).to_dict()
                Global.ICD.text_dict = pd.Series(
                    Global.ICD.df.CodeWithoutAsterisk.values, Global.ICD.df.Title
                ).to_dict()
                Global.ICD.ready = True

    def perform_operation(self, text):
        self.icd[self.icd[9].str.contains("Shigellosis")][[6]]
        return None


class Thesaurus(Operation):
    def __init__(self, probability):
        Operation.__init__(self, probability)

    def perform_operation(self, text):
        from nltk.corpus import wordnet as wn

        synonyms = []
        for syn in wn.synsets("heart"):
            for lemma in syn.lemmas():
                synonyms.append(lemma.name())
        pass


class SNOMED(Operation):
    def __init__(self, probability, snomed_core_file="SNOMEDCT_CORE_SUBSET_202102.txt"):
        Operation.__init__(self, probability)
        self.snomed_core_file = snomed_core_file
        userhome = os.path.expanduser("~")
        augmentext_home = os.path.join(userhome, ".augmentext")
        if not os.path.exists(augmentext_home):
            os.mkdir(augmentext_home)
        snomed_home = os.path.join(augmentext_home, "snomed")
        if not os.path.exists(snomed_home):
            os.mkdir(snomed_home)
        snomed_core_full_path = os.path.join(snomed_home, self.snomed_core_file)
        if os.path.isfile(snomed_core_full_path):
            md5_calculated = hashlib.md5(open(snomed_core_full_path, "rb").read()).hexdigest()
            assert md5_calculated == Global.SNOMED.md5
            Global.SNOMED.csv_content = pd.read_csv(snomed_core_full_path, sep="|")
            csv_content = pd.read_csv(snomed_core_full_path, sep="|")
            self.terms = csv_content["SNOMED_FSN"].str.replace(" \(disorder\)| \(procedure\)| \(finding\)", "")
            self.cids = csv_content["SNOMED_CID"]
            self.umls_cuis = csv_content["UMLS_CUI"]
            del csv_content
            Global.SNOMED.ready = True
        else:
            print("SNOMED Core not found. Expected a file here: %s" % snomed_core_full_path)
        snomed_full = pd.read_csv(os.path.join(snomed_home, "sct2_Description_Full-en_INT_20210131.txt"), sep="\t")[
            ["conceptId", "term", "active"]
        ]
        snomed_full.drop(snomed_full[snomed_full.active == 0].index, inplace=True)
        snomed_full.term = snomed_full.term.str.replace(" \(disorder\)| \(procedure\)| \(finding\)", "")
        snomed_full.drop_duplicates(subset=["term"], inplace=True)
        snomed_full.dropna(inplace=True)
        Global.SNOMED.snomed_full = snomed_full
        del snomed_full

    def perform_operation(self, text):
        if Global.SNOMED.ready:
            return text
        else:
            return text


class MeSH:
    def __init__(self, probability):
        Operation.__init__(self, probability)
        userhome = os.path.expanduser("~")
        augmentext_home = os.path.join(userhome, ".augmentext")
        mesh_home = os.path.join(augmentext_home, "mesh")
        mesh_file_name = "d2021.bin"
        with open(os.path.join(mesh_home, mesh_file_name)) as f:
            mesh_content = f.read().split("\n\n")
        mesh_content = mesh_content[0:-1]
        self.mesh_dict = {}
        for mesh_entry in mesh_content:
            mesh_heading = mesh_entry.split("MH = ")[1].split("\n")[0]
            entries = []
            for line in mesh_entry.split("\n"):
                if line.startswith("ENTRY = "):
                    line = line.split("ENTRY = ")[1]
                    if "|" in line:
                        line = line.split("|")[0]
                    entries.append(line.lower())
            entries.append(mesh_heading.lower())
            for entry in entries:
                t_entries = entries.copy()
                t_entries.remove(entry)
                self.mesh_dict[entry] = t_entries

    def perform_operation(self, text):
        words = word_tokenize(text)
        words_in_mesh = []
        for word in words:
            if word in self.mesh_dict:
                if len(self.mesh_dict[word]) >= 1:
                    words_in_mesh.append(word)
        if len(words_in_mesh) >= 1:
            word_to_replace = random.choice(words_in_mesh)
            replace_with = random.choice(self.mesh_dict[word_to_replace])
            return text.replace(word_to_replace, replace_with)
        else:
            return text


class Icd9ToIcd10(Operation):
    pass


class TallManLettering(Operation):
    def __init__(self, probability):
        Operation.__init__(self, probability)

    def perform_operation(self, text):
        pass


def get_neighbouring_character(char, aggressive):
    neighbours = {
        "q": list("wsa"),
        "w": list("qeasd"),
        "e": list("wrsdf"),
        "r": list("etdfg"),
        "t": list("rzfgh"),
        "y": list("tughj"),
        "u": list("yihjk"),
        "i": list("uojkl"),
        "o": list("ipkl"),
        "p": list("ol"),
        "a": list("qwsy"),
        "s": list("awdx"),
        "d": list("sefc"),
        "f": list("drgv"),
        "g": list("fthb"),
        "h": list("gzjn"),
        "j": list("huknm"),
        "k": list("jilm"),
        "l": list("kop"),
        "z": list("asx"),
        "x": list("zsdc"),
        "c": list("xdfv"),
        "v": list("cfgb"),
        "b": list("vghn"),
        "n": list("bhjm"),
        "m": list("njk"),
        "Q": list("WSA"),
        "W": list("QEASD"),
        "E": list("WRSDF"),
        "R": list("ETDFG"),
        "T": list("RZFGH"),
        "Y": list("TUGHJ"),
        "U": list("YIHJK"),
        "I": list("UOJKL"),
        "O": list("IPKL"),
        "P": list("OL"),
        "A": list("QWSY"),
        "S": list("AWDX"),
        "D": list("SEFC"),
        "F": list("DRGV"),
        "G": list("FTHB"),
        "H": list("GZJN"),
        "J": list("HUKNM"),
        "K": list("JILM"),
        "L": list("KOP"),
        "Z": list("ASX"),
        "X": list("ZSDC"),
        "C": list("XDFV"),
        "V": list("CFGB"),
        "B": list("VGHN"),
        "N": list("BHJM"),
        "M": list("NJK"),
    }
    neighbours_less_aggressive = {
        "q": list("w"),
        "w": list("qe"),
        "e": list("wr"),
        "r": list("et"),
        "t": list("ry"),
        "y": list("tu"),
        "u": list("yi"),
        "i": list("uo"),
        "o": list("ip"),
        "p": list("o"),
        "a": list("s"),
        "s": list("ad"),
        "d": list("sf"),
        "f": list("dg"),
        "g": list("fh"),
        "h": list("gj"),
        "j": list("hk"),
        "k": list("jl"),
        "l": list("k"),
        "z": list("x"),
        "x": list("zc"),
        "c": list("xv"),
        "v": list("cb"),
        "b": list("vn"),
        "n": list("bm"),
        "m": list("n"),
        "Q": list("W"),
        "W": list("QE"),
        "E": list("WR"),
        "R": list("ET"),
        "T": list("RY"),
        "Y": list("TU"),
        "U": list("YI"),
        "I": list("UO"),
        "O": list("IP"),
        "P": list("O"),
        "A": list("S"),
        "S": list("AD"),
        "D": list("SF"),
        "F": list("DG"),
        "G": list("FH"),
        "H": list("GJ"),
        "J": list("HK"),
        "K": list("JL"),
        "L": list("K"),
        "Z": list("X"),
        "X": list("ZC"),
        "C": list("XV"),
        "V": list("CB"),
        "B": list("VN"),
        "N": list("BM"),
        "M": list("N"),
    }
    return neighbours[char] if aggressive == True else neighbours_less_aggressive[char]


def convert_numbers_to_words(n):
    zero_to_nineteen = [
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
    ]
    if n in range(0, 19):
        return zero_to_nineteen[n]
    else:
        return n


ZERO_TO_ONE_HUNDRED_NUMERIC = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
    "twenty-one",
    "twenty-two",
    "twenty-three",
    "twenty-four",
    "twenty-five",
    "twenty-six",
    "twenty-seven",
    "twenty-eight",
    "twenty-nine",
    "thirty",
    "thirty-one",
    "thirty-two",
    "thirty-three",
    "thirty-four",
    "thirty-five",
    "thirty-six",
    "thirty-seven",
    "thirty-eight",
    "thirty-nine",
    "forty",
    "forty-one",
    "forty-two",
    "forty-three",
    "forty-four",
    "forty-five",
    "forty-six",
    "forty-seven",
    "forty-eight",
    "forty-nine",
    "fifty",
    "fifty-one",
    "fifty-two",
    "fifty-three",
    "fifty-four",
    "fifty-five",
    "fifty-six",
    "fifty-seven",
    "fifty-eight",
    "fifty-nine",
    "sixty",
    "sixty-one",
    "sixty-two",
    "sixty-three",
    "sixty-four",
    "sixty-five",
    "sixty-six",
    "sixty-seven",
    "sixty-eight",
    "sixty-nine",
    "seventy",
    "seventy-one",
    "seventy-two",
    "seventy-three",
    "seventy-four",
    "seventy-five",
    "seventy-six",
    "seventy-seven",
    "seventy-eight",
    "seventy-nine",
    "eighty",
    "eighty-one",
    "eighty-two",
    "eighty-three",
    "eighty-four",
    "eighty-five",
    "eighty-six",
    "eighty-seven",
    "eighty-eight",
    "eighty-nine",
    "ninety",
    "ninety-one",
    "ninety-two",
    "ninety-three",
    "ninety-four",
    "ninety-five",
    "ninety-six",
    "ninety-seven",
    "ninety-eight",
    "ninety-nine",
]
ZERO_TO_ONE_HUNDRED_TEXT = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "thirteen": "13",
    "fourteen": "14",
    "fifteen": "15",
    "sixteen": "16",
    "seventeen": "17",
    "eighteen": "18",
    "nineteen": "19",
    "twenty": "20",
    "twenty-one": "21",
    "twenty-two": "22",
    "twenty-three": "23",
    "twenty-four": "24",
    "twenty-five": "25",
    "twenty-six": "26",
    "twenty-seven": "27",
    "twenty-eight": "28",
    "twenty-nine": "29",
    "thirty": "30",
    "thirty-one": "31",
    "thirty-two": "32",
    "thirty-three": "33",
    "thirty-four": "34",
    "thirty-five": "35",
    "thirty-six": "36",
    "thirty-seven": "37",
    "thirty-eight": "38",
    "thirty-nine": "39",
    "forty": "40",
    "forty-one": "41",
    "forty-two": "42",
    "forty-three": "43",
    "forty-four": "44",
    "forty-five": "45",
    "forty-six": "46",
    "forty-seven": "47",
    "forty-eight": "48",
    "forty-nine": "49",
    "fifty": "50",
    "fifty-one": "51",
    "fifty-two": "52",
    "fifty-three": "53",
    "fifty-four": "54",
    "fifty-five": "55",
    "fifty-six": "56",
    "fifty-seven": "57",
    "fifty-eight": "58",
    "fifty-nine": "59",
    "sixty": "60",
    "sixty-one": "61",
    "sixty-two": "62",
    "sixty-three": "63",
    "sixty-four": "64",
    "sixty-five": "65",
    "sixty-six": "66",
    "sixty-seven": "67",
    "sixty-eight": "68",
    "sixty-nine": "69",
    "seventy": "70",
    "seventy-one": "71",
    "seventy-two": "72",
    "seventy-three": "73",
    "seventy-four": "74",
    "seventy-five": "75",
    "seventy-six": "76",
    "seventy-seven": "77",
    "seventy-eight": "78",
    "seventy-nine": "79",
    "eighty": "80",
    "eighty-one": "81",
    "eighty-two": "82",
    "eighty-three": "83",
    "eighty-four": "84",
    "eighty-five": "85",
    "eighty-six": "86",
    "eighty-seven": "87",
    "eighty-eight": "88",
    "eighty-nine": "89",
    "ninety": "90",
    "ninety-one": "91",
    "ninety-two": "92",
    "ninety-three": "93",
    "ninety-four": "94",
    "ninety-five": "95",
    "ninety-six": "96",
    "ninety-seven": "97",
    "ninety-eight": "98",
    "ninety-nine": "99",
    "one hundred": "100",
}
ENGLISH_STOP_WORDS = set([
    "a",
    "about",
    "above",
    "across",
    "after",
    "afterwards",
    "again",
    "against",
    "ain",
    "all",
    "almost",
    "alone",
    "along",
    "already",
    "also",
    "although",
    "always",
    "am",
    "among",
    "amongst",
    "amoungst",
    "amount",
    "an",
    "and",
    "another",
    "any",
    "anyhow",
    "anyone",
    "anything",
    "anyway",
    "anywhere",
    "are",
    "aren",
    "around",
    "as",
    "at",
    "back",
    "be",
    "became",
    "because",
    "become",
    "becomes",
    "becoming",
    "been",
    "before",
    "beforehand",
    "behind",
    "being",
    "below",
    "beside",
    "besides",
    "between",
    "beyond",
    "bill",
    "both",
    "bottom",
    "but",
    "by",
    "call",
    "can",
    "cannot",
    "cant",
    "co",
    "con",
    "could",
    "couldn",
    "couldnt",
    "cry",
    "d",
    "de",
    "describe",
    "detail",
    "did",
    "didn",
    "do",
    "does",
    "doesn",
    "doing",
    "don",
    "done",
    "down",
    "due",
    "during",
    "each",
    "eg",
    "eight",
    "either",
    "eleven",
    "else",
    "elsewhere",
    "empty",
    "enough",
    "etc",
    "even",
    "ever",
    "every",
    "everyone",
    "everything",
    "everywhere",
    "except",
    "few",
    "fifteen",
    "fify",
    "fill",
    "find",
    "fire",
    "first",
    "five",
    "for",
    "former",
    "formerly",
    "forty",
    "found",
    "four",
    "from",
    "front",
    "full",
    "further",
    "get",
    "give",
    "go",
    "had",
    "hadn",
    "has",
    "hasn",
    "hasnt",
    "have",
    "haven",
    "having",
    "he",
    "hence",
    "her",
    "here",
    "hereafter",
    "hereby",
    "herein",
    "hereupon",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "however",
    "hundred",
    "i",
    "ie",
    "if",
    "in",
    "inc",
    "indeed",
    "interest",
    "into",
    "is",
    "isn",
    "it",
    "its",
    "itself",
    "just",
    "keep",
    "last",
    "latter",
    "latterly",
    "least",
    "less",
    "ll",
    "ltd",
    "m",
    "ma",
    "made",
    "many",
    "may",
    "me",
    "meanwhile",
    "might",
    "mightn",
    "mill",
    "mine",
    "more",
    "moreover",
    "most",
    "mostly",
    "move",
    "much",
    "must",
    "mustn",
    "my",
    "myself",
    "name",
    "namely",
    "needn",
    "neither",
    "never",
    "nevertheless",
    "next",
    "nine",
    "no",
    "nobody",
    "none",
    "noone",
    "nor",
    "not",
    "nothing",
    "now",
    "nowhere",
    "o",
    "of",
    "off",
    "often",
    "on",
    "once",
    "one",
    "only",
    "onto",
    "or",
    "other",
    "others",
    "otherwise",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "part",
    "per",
    "perhaps",
    "please",
    "put",
    "rather",
    "re",
    "s",
    "same",
    "see",
    "seem",
    "seemed",
    "seeming",
    "seems",
    "serious",
    "several",
    "shan",
    "she",
    "should",
    "shouldn",
    "show",
    "side",
    "since",
    "sincere",
    "six",
    "sixty",
    "so",
    "some",
    "somehow",
    "someone",
    "something",
    "sometime",
    "sometimes",
    "somewhere",
    "still",
    "such",
    "system",
    "t",
    "take",
    "ten",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "thence",
    "there",
    "thereafter",
    "thereby",
    "therefore",
    "therein",
    "thereupon",
    "these",
    "they",
    "thick",
    "thin",
    "third",
    "this",
    "those",
    "though",
    "three",
    "through",
    "throughout",
    "thru",
    "thus",
    "to",
    "together",
    "too",
    "top",
    "toward",
    "towards",
    "twelve",
    "twenty",
    "two",
    "un",
    "under",
    "until",
    "up",
    "upon",
    "us",
    "ve",
    "very",
    "via",
    "was",
    "wasn",
    "we",
    "well",
    "were",
    "weren",
    "what",
    "whatever",
    "when",
    "whence",
    "whenever",
    "where",
    "whereafter",
    "whereas",
    "whereby",
    "wherein",
    "whereupon",
    "wherever",
    "whether",
    "which",
    "while",
    "whither",
    "who",
    "whoever",
    "whole",
    "whom",
    "whose",
    "why",
    "will",
    "with",
    "within",
    "without",
    "won",
    "would",
    "wouldn",
    "y",
    "yet",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
])
OLD_DISEASSE = {
    "Ablepsy": "Blindness",
    "Ague": "Malarial Fever",
    "American plague": "Yellow fever",
    "Anasarca": "Generalized massive edema",
    "Aphonia": "Laryngitis",
    "Aphtha": "The infant disease thrush",
    "Apoplexy": "Paralysis due to stroke",
    "Asphyxia/Asphicsia": "Cyanotic and lack of oxygen",
    "Atrophy": "Wasting away or diminishing in size",
    "Bad Blood": "Syphilis",
    "Bilious fever": "Typhoid: malaria: hepatitis or elevated temperature and bile emesis",
    "Biliousness": "Jaundice associated with liver disease",
    "Black plague or death": "Bubonic plague",
    "Black fever": "Acute infection with high temperature and dark red skin lesions and high mortality rate",
    "Black pox": "Black Smallpox",
    "Black vomit": "Vomiting old black blood due to ulcers or yellow fever",
    "Blackwater Fever": "Dark urine associated with high temperature",
    "Bladder in Throat": "Diphtheria (Seen on death certificates)",
    "Blood poisoning": "Bacterial infection; septicemia",
    "Bloody flux": "Bloody stools",
    "Bloody sweat": "Sweating sickness",
    "Bone shave": "Sciatica",
    "Brain fever": "Meningitis",
    "Breakbone": "Dengue fever",
    "Bright's disease": "Chronic inflammatory disease of kidneys",
    "Bronze John": "Yellow fever",
    "Bule Boil": "tumor or swelling",
    "Cachexia": "Malnutrition",
    "Caco Gastric": "Upset stomach",
    "Casopisy": "Irregular pulse",
    "Caduceus": "Subject to falling sickness or epilepsy",
    "Camp Fever": "Typhus; aka Camp diarrhea",
    "Canine Madness": "Rabies: hydrophobia",
    "Canker": "Ulceration of mouth or lips or herpes simplex",
    "Catalepsy": "Seizures / trances",
    "Catarrhal": "Nose and throat discharge from cold or allergy",
    "Cerebritis": "Inflammation of cerebrum or lead poisoning",
    "Chilblain": "Swelling of extremities caused by exposure to cold",
    "Childbed Fever": "Infection following birth of a child",
    "Chin Cough": "Whooping cough",
    "Chlorosis": "Iron deficiency anemia",
    "Cholera": "Acute severe contagious diarrhea with intestinal lining sloughing",
    "Cholera morbus": "Characterized by nausea: vomiting: abdominal cramps: elevated temperature: etc. Could be appendicitis",
    "Cholecystitis": "inflammation of the gallbladder",
    "Cholelithiasis": "Gallstones",
    "Chorea": "Disease characterized by convulsions: contortions and dancing",
    "Cold Plague": "Ague which is characterized by chills",
    "Colic": "An abdominal pain and cramping",
    "Congestive Chills": "Malaria",
    "Consumption": "Tuberculosis",
    "Congestion": "Any collection of fluid in an organ: like the lungs",
    "Congestive Fever": "Malaria",
    "Corruption": "Infection",
    "Coryza": "A cold",
    "Costiveness": "Constipation",
    "Cramp Colic": "Appendicitis",
    "Crop Sickness": "Over Extended Stomach",
    "Croup Laryngitis": "diphtheria: or strep throat",
    "Cyanosis": "Dark skin color from lack of oxygen in blood",
    "Cynanche": "Diseases of throat",
    "Cystitis": "Inflammation of the bladder",
    "Day Fever": "Fever lasting one day; sweating sickness",
    "Debility": "Lack of movement or staying in bed",
    "Decrepitude": "Feebleness due to old age",
    "Delirium tremens": "Hallucinations due to alcoholism",
    "Dengue": "Infectious fever endemic to East Africa",
    "Dentition": "Cutting of teeth",
    "Deplumation": "Tumor of the eyelids which causes hair loss",
    "Diary Fever": "A fever that lasts one day",
    "Diphtheria": "Contagious disease of the throat",
    "Distemper": "Usually animal disease with malaise: discharge from nose and throat: anorexia",
    "Dock Fever": "Yellow fever",
    "Dropsy": "Edema (swelling): often caused by kidney disease (Glomerulonephritis) or heart disease",
    "Dropsy of the Brain": "Encephalitis",
    "Dry Bellyache": "Lead poisoning",
    "Dyscrasy": "An abnormal body condition",
    "Dysentery": "Inflammation of colon with frequent passage",
    "Dysorexy": "Reduced appetite of mucous and blood",
    "Dyspepsia": "Indigestion and heartburn. Heart attack symptoms",
    "Dysury": "Difficulty in urination",
    "Eclampsia": "Symptoms of epilepsy: convulsions during labor",
    "Ecstasy": "A form of catalepsy characterized by loss of reason",
    "Edema Nephrosis": "swelling of tissues",
    "Edema of lungs": "Congestive heart failure: a form of dropsy",
    "Eel thing": "Erysipelas",
    "Elephantiasis": "A form of leprosy",
    "Encephalitis": "Swelling of brain; aka sleeping sickness",
    "Enteric Fever": "Typhoid fever",
    "Enterocolitis": "Inflammation of the intestines",
    "Enteritis": "Inflations of the bowels",
    "Epistaxis": "Nosebleed",
    "Erysipelas": "Contagious skin disease: due to Streptococci with vesicular and bullous lesions",
    "Extravasated Blood": "Rupture of a blood vessel",
    "Falling sickness": "Epilepsy",
    "Fatty Liver": "Cirrhosis of liver",
    "Fits": "Sudden attack or seizure of muscle activity",
    "Flux": "An excessive flow or discharge of fluid like hemorrhage or diarrhea",
    "Flux of Humour": "Circulation",
    "French Pox": "Syphilis",
    "Gathering": "A collection of pus",
    "Glandular Fever": "Mononucleosis",
    "Great Pox": "Syphilis",
    "Green Fever / Sickness": "Anemia",
    "Grippe / Grip": "Influenza like symptoms",
    "Grocer's Itch": "Skin disease caused by mites in sugar or flour",
    "Heart Sickness": "Condition caused by loss of salt from body",
    "Heat Stroke": "Body temperature elevates because of surrounding environment temperature and body does not perspire to reduce temperature. Coma and death result if notreversed",
    "Hectical Complaint": "Recurrent fever",
    "Hematemesis": "Vomiting blood",
    "Hematuria": "Bloody urine",
    "Hemiplegia": "Paralysis of one side of body",
    "Hip Gout": "Osteomyelitis",
    "Horrors": "Delirium tremens",
    "Hydrocephalus": "Enlarged head: water on the brain",
    "Hydropericardium": "Heart dropsy",
    "Hydrophobia": "Rabies",
    "Hydrothorax": "Dropsy in chest",
    "Hypertrophic": "Enlargement of organ: like the heart",
    "Impetigo": "Contagious skin disease characterized by pustules",
    "Inanition": "Physical condition resulting from lack of food",
    "Infantile Paralysis": "Polio",
    "Intestinal colic": "Abdominal pain due to improper diet",
    "Jail Fever": "Typhus",
    "Jaundice": "Condition caused by blockage of intestines",
    "King's Evil": "Tuberculosis of neck and lymph glands",
    "Keuchhusten": "Whooping cough",
    "La Grippe": "Influenza",
    "Lockjaw": "Tetanus or infectious disease affecting the muscles of the neck and jaw. Untreated: it is fatal in 8 days",
    "Long Sickness": "Tuberculosis",
    "Lues Disease": "Syphilis",
    "Lues Venera": "Venereal disease",
    "Lumbago": "Back pain",
    "Lung Fever": "Pneumonia",
    "Lung Sickness": "Tuberculosis",
    "Lying in": "Time of delivery of infant",
    "Malignant Sore Throat": "Diphtheria",
    "Mania": "Insanity",
    "Marasmus": "Progressive wasting away of body: like malnutrition",
    "Membranous": "Croup Diphtheria",
    "Meningitis": "Inflations of brain or spinal cord",
    "Metritis": "Inflammation of uterus or purulent vaginal discharge",
    "Miasma": "Poisonous vapors thought to infect the air",
    "Milk Fever": "Disease from drinking contaminated milk: like undulant fever or brucellosis",
    "Milk Leg": "Postpartum thrombophlebitis",
    "Milk Sickness": "Disease from milk of cattle which had eaten poisonous weeds",
    "Mormal": "Gangrene",
    "Morphew": "Scurvy blisters on the body",
    "Mortification": "Gangrene of necrotic tissue",
    "Myelitis": "Inflammation of the spine",
    "Myocarditis": "Inflammation of heart muscles",
    "Necrosis": "Mortification of bones or tissue",
    "Nephrosis": "Kidney degeneration",
    "Nephritis": "Inflammation of kidneys",
    "Nervous Prostration": "Extreme exhaustion from inability to control physical and mental activities",
    "Neuralgia": "Described as discomfort: such as Headache was neuralgia in head",
    "Nostalgia": "Homesickness",
    "Palsy": "Paralysis or uncontrolled movement of controlled muscles",
    "Paroxysm": "Convulsion",
    "Pemphigus": "Skin disease of watery blisters",
    "Pericarditis": "Inflammation of heart",
    "Peripneumonia": "Inflammation of lungs",
    "Peritonitis": "Inflammation of abdominal area",
    "Petechial Fever": "Fever characterized by skin spotting",
    "Phthiriasis": "Lice infestation",
    "Phthisis Chronic": "wasting away or a name for tuberculosis",
    "Plague": "An acute febrile highly infectious disease with a high fatality rate",
    "Pleurisy": "Any pain in the chest area with each breath",
    "Podagra": "Gout",
    "Poliomyelitis": "Polio",
    "Potter's Asthma": "Fibroid phthisis",
    "Pott's Disease": "Tuberculosis of spine",
    "Puerperal Exhaustion": "Death due to childbirth",
    "Puerperal Fever": "Elevated temperature after giving birth to an infant",
    "Puking Fever": "Milk sickness",
    "Putrid Fever": "Diphtheria",
    "Quinsy": "Tonsillitis",
    "Remitting Fever": "Malaria",
    "Rheumatism": "Any disorder associated with pain in joints",
    "Rickets Disease": "of skeletal system",
    "Rose Cold": "Hay fever or nasal symptoms of an allergy",
    "Rotanny Fever": "(Child's disease) ???",
    "Rubeola": "German measles",
    "Sanguineous Crust": "Scab",
    "Scarlatina": "Scarlet fever",
    "Scarlet Fever": "A disease characterized by red rash",
    "Scarlet Rash": "Roseola",
    "Sciatica": "Rheumatism in the hips",
    "Scirrhous": "Cancerous tumors",
    "Scotomy": "Dizziness: nausea and dimness of sight",
    "Scrivener's palsy": "Writer's cramp",
    "Screws": "Rheumatism",
    "Scrofula": "Tuberculosis of neck lymph glands. Progresses slowly with abscesses and fistulas develop. Young person's disease",
    "Scrumpox": "Skin disease: impetigo",
    "Scurvy": "Lack of vitamin C. Symptoms of weakness: spongy gums and hemorrhages under skin",
    "Septicemia": "Blood poisoning",
    "Shakes": "Delirium tremens",
    "Shaking": "Chills: ague",
    "Shingles": "Viral disease with skin blisters",
    "Ship Fever": "Typhus",
    "Psoriasis": "Inflammation of the brain due to sun exposure",
    "Sloes": "Milk sickness",
    "Small pox": "Contagious disease with fever and blisters",
    "Softening of brain": "Result of stroke or hemorrhage in the brain: with an end result of the tissue softening in that area",
    "Sore Throat Distemper": "Diphtheria or quinsy",
    "Spanish Influenza": "Epidemic influenza",
    "Spasms": "Sudden involuntary contraction of muscle or group of muscles: like a convulsion",
    "Spina Bifida": "Deformity of spine",
    "Spotted Fever": "Either typhus or meningitis",
    "Sprue": "Tropical disease characterized by intestinal disorders and sore throat",
    "St. Anthony's Fire": "Also erysipelas: but named so because of affected skin areas are bright red in appearance",
    "St. Vitus’ Dance": "Ceaseless occurrence of rapid complex jerking movements performed involuntarily",
    "Stomatitis": "Inflammation of the mouth",
    "Stranger's Fever": "Yellow fever",
    "Strangery": "Rupture",
    "Sudor Anglicus": "Sweating sickness",
    "Summer Complaint": "Diarrhea: usually in infants caused by spoiled milk",
    "Sunstroke": "Uncontrolled elevation of body temperature due to environment heat. Lack of sodium in the body is a predisposing cause",
    "Swamp Sickness": "Could be malaria: typhoid or encephalitis",
    "Sweating Sickness": "Infectious and fatal disease common to UK in 15th century",
    "Tetanus": "Infectious fever characterized by high fever: headache and dizziness",
    "Thrombosis": "Blood clot inside blood vessel",
    "Thrush": "Childhood disease characterized by spots on mouth: lips and throat",
    "Tick Fever": "Rocky mountain spotted fever",
    "Toxemia of Pregnancy": "Eclampsia",
    "Trench Mouth": "Painful ulcers found along gum line: Caused by poor nutrition and poor hygiene",
    "Tussis Convulsiva": "Whooping cough",
    "Typhus": "Infectious fever characterized high fever: headache: and dizziness",
    "Variola": "Smallpox",
    "Venesection": "Bleeding",
    "Viper's Dance": "St. Vitus Dance",
    "Water on Brain": "Enlarged head",
    "White Swelling": "Tuberculosis of the bone",
    "Winter Fever": "Pneumonia",
    "Womb Fever": "Infection of the uterus",
    "Worm Fit": "Convulsions associated with teething: worms: elevated temperature or diarrhea",
    "Yellow Jacket": "Yellow fever",
}
