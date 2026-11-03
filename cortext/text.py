import nltk


class Text:
    def __init__(self, raw_text):
        self.raw_text = raw_text

    def parse(self):
        sentences = nltk.sent_tokenize(self.raw_text)
        tokens = [nltk.word_tokenize(sentence) for sentence in sentences]
        self.tagged_sentences = [self.tag(words) for words in tokens]
        return self

    def tag(self, sentence):
        initial_tagged_words = nltk.pos_tag(sentence)
        tagged_words = []
        consecutive_names = []
        last_tag = None
        for tagged_word in initial_tagged_words:
            if tagged_word[1].startswith("NNP"):
                consecutive_names.append(tagged_word[0])
                last_tag = tagged_word[1]
            else:
                if consecutive_names:
                    tagged_words.append((" ".join(consecutive_names), last_tag))
                    consecutive_names = []
                tagged_words.append(tagged_word)
        if consecutive_names:
            tagged_words.append((" ".join(consecutive_names), last_tag))
        return tagged_words
