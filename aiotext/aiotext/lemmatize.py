import nltk
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer


def lemmatize(tokens):
    tag_map = {
        "CC": None,
        "CD": wn.NOUN,
        "DT": None,
        "EX": wn.ADV,
        "FW": None,
        "IN": wn.ADV,
        "JJ": wn.ADJ,
        "JJR": wn.ADJ,
        "JJS": wn.ADJ,
        "LS": None,
        "MD": None,
        "NN": wn.NOUN,
        "NNS": wn.NOUN,
        "NNP": wn.NOUN,
        "NNPS": wn.NOUN,
        "PDT": wn.ADJ,
        "POS": None,
        "PRP": None,
        "PRP$": None,
        "RB": wn.ADV,
        "RBR": wn.ADV,
        "RBS": wn.ADV,
        "RP": wn.ADJ,
        "SYM": None,
        "TO": None,
        "UH": None,
        "VB": wn.VERB,
        "VBD": wn.VERB,
        "VBG": wn.VERB,
        "VBN": wn.VERB,
        "VBP": wn.VERB,
        "VBZ": wn.VERB,
        "WDT": None,
        "WP": None,
        "WP$": None,
        "WRB": None,
        "$": None,
        "#": None,
        "“": None,
        "”": None,
        "(": None,
        ")": None,
        ",": None,
        ".": None,
        ":": None,
    }

    lemmatizer = WordNetLemmatizer()

    tag_tuples = nltk.pos_tag(tokens)

    penn_keys = list(tag_map.keys())
    wn_tags = []

    for word, tag in tag_tuples:
        if tag in penn_keys:
            wn_tags.append((word, tag_map[tag]))
        else:
            wn_tags.append((word, None))

    output = []
    for word, tag in wn_tags:
        if tag == None:
            output.append(word)
        else:
            output.append(lemmatizer.lemmatize(word, tag))

    return output
