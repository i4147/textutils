import cortext.classifier


class Visualizer:
    def __init__(self, text, api_config, cache=None):
        self.text = text
        self._classifier = cortext.classifier.Classifier()
        self._api_config = api_config
        self._visualized_dict = {}
        self._visualized_words = {}
        self._cache = cache

    def classify_words(self):
        classified_words = {}
        classified = []
        for sentence in self.text.tagged_sentences:
            classified.append([])
            for tagged_word in sentence:
                if self._cache and self._cache.has(tagged_word[0]):
                    classified_words[tagged_word[0]] = self._cache.get(tagged_word[0])
                elif tagged_word[0] not in classified_words:
                    classified_words[tagged_word[0]] = self._classifier.classify_word(tagged_word)
                    if self._cache:
                        self._cache.set(tagged_word[0], classified_words[tagged_word[0]])
                classified[-1].append(classified_words[tagged_word[0]])
        return classified

    def visualize_words(self):
        classified = self.classify_words()
        visualized = []
        for sentence in classified:
            visualized.append([])
            for classified in sentence:
                if classified.word not in self._visualized_words:
                    self._visualized_dict[classified.word] = classified.extract_data(self._api_config)
                visualized[-1].append(self._visualized_dict[classified.word])
        self._visualized_words = visualized
        return visualized

    def visualize_sentences(self):
        if self._visualized_words is None:
            self.visualize_words()
        return [
            self._sentence_classifier.classify(sentence, visualized_words).generate(sentence, visualized_words)
            for sentence, visualized_words in zip(self.text.tagged_sentences, self._visualized_words)
        ]
