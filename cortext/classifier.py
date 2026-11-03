import cortext.word_types as word_types
from nltk.corpus import wordnet as wn
import urllib.request
import json


class Classifier:
    def classify_word(self, tagged_word):
        word, tag = tagged_word
        if tag == "JJ":
            return self.classify_adjective(word)
        elif tag.startswith("VB"):
            print(dir(self))
            return self.classify_verb(word)
        elif tag.startswith("NNP"):
            return self.classify_name(word)
        elif tag.startswith("N"):
            return self.classify_noun(word)
        else:
            return word_types.Unknown(word)

    def classify_adjective(self, word):
        for synset in wn.synsets(word):
            if synset.lexname() == "noun.attribute" and "color" in synset.definition():
                return word_types.Color(word)
        return word_types.Adjective(word)

    def classify_verb(self, word):
        for synset in wn.synsets(word):
            if synset.lexname() in ["verb.motion", "verb.cognition"]:
                return word_types.Verb(word)
        return word_types.Unknown(word)

    def classify_noun(self, word):
        return word_types.Noun(word)

    def classify_name(self, word):
        return self.fetch_dbpedia_json(word)

    def fetch_dbpedia_json(self, name):
        original_name, name = name, name.replace(" ", "_")
        name = name[0] + name[1:].lower()
        u = "http://dbpedia.org/data/{0}.json".format(name)
        data = urllib.request.urlopen(u)
        json_data = json.loads(data.read().decode("utf8"))
        thumbnail_url = json_data["http://dbpedia.org/resource/{0}".format(name)][
            "http://dbpedia.org/ontology/thumbnail"
        ][0]["value"]
        abstracts = [
            abstract["value"]
            for abstract in json_data["http://dbpedia.org/resource/{0}".format(name)][
                "http://dbpedia.org/ontology/abstract"
            ]
            if abstract["lang"] == "en"
        ]
        if abstracts:
            return word_types.Celebrity(original_name, abstracts[0], thumbnail_url)
        else:
            return word_types.Unknown(original_name)
