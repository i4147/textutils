from operator import index
import re
import os
import sys
import json
import pandas as pd
import numpy as np
import nltk

nltk.download("punkt", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("omw-1.4", quiet=True)
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
import unicodedata
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

path = os.path.dirname(os.path.abspath(__file__))
abbreviations_path = os.path.join(path, "data", "abbreviations_wordlist.json")
stopwords = set(
    """
a about above across after afterwards again against all almost alone along
already also although always am among amongst amount an and another any anyhow
anyone anything anyway anywhere are around as at

back be became because become becomes becoming been before beforehand behind
being below beside besides between beyond both bottom but by

call can cannot ca could

did do does doing done down due during

each eight either eleven else elsewhere empty enough even ever every
everyone everything everywhere except

few fifteen fifty first five for former formerly forty four from front full
further

get give go

had has have he hence her here hereafter hereby herein hereupon hers herself
him himself his how however hundred

i if in indeed into is it its itself

keep

last latter latterly least less

just

made make many may me meanwhile might mine more moreover most mostly move much
must my myself

name namely neither nevertheless next nine noone 
nothing now nowhere

of off often on once one only onto or other others otherwise our ours ourselves
out over own o oo

part per perhaps please put

quite

rather re really regarding

same say see seem seemed seeming seems serious several she should show side
since six sixty so some somehow someone something sometime sometimes somewhere
still such

take ten than that the their them themselves then thence there thereafter
thereby therefore therein thereupon these they third this those though three
through throughout thru thus to together too top toward towards twelve twenty
two

under until up unless upon us used using

various very very via was we well were what whatever when whence whenever where
whereafter whereas whereby wherein whereupon wherever whether which while
whither who whoever whole whom whose why will with within without would

yet you your yours yourself yourselves
""".split()
)


class Counter(object):
    def __init__(self, text=None):
        super(Counter, self).__init__()
        self.text = text

    def __repr__(self):
        return f'Counter(text="{self.text}")'

    def count_words(self):
        x = self.text.lower()
        length = len(str(x).split())
        return length

    def count_characters(self):
        x = self.text.lower()
        x_splitted = x.split()
        x = "".join(x_splitted)
        return len(x)

    def count_avg_wordlength(self):
        avg_count = self.count_characters() / self.count_words()
        return avg_count

    def count_stopwords(self):
        x = self.text.lower()
        lst = len([t for t in x.split() if t in stopwords])
        return lst

    def count_hashtags(self):
        x = self.text
        lst = len([t for t in x.split() if t.startswith("#")])
        return lst

    def count_mentions(self):
        x = self.text
        lst = len([t for t in x.split() if t.startswith("@")])
        return lst

    def count_digits(self):
        x = self.text
        digits = re.findall(r"[0-9]+", x)
        return len(digits)

    def count_uppercase_words(self):
        x = self.text
        return len([word for word in x.split() if word.isupper()])

    def count_whitespace(self):
        count = 0
        x = self.text
        for char in x:
            if char == " ":
                count += 1
        return count

    def count_vowels(self):
        count = 0
        x = self.text
        for char in x:
            if char in ["a", "e", "i", "o", "u"]:
                count += 1
        return count

    def count_consonants(self):
        count = 0
        x = self.text
        for char in x:
            if char not in ["a", "e", "i", "o", "u"]:
                count += 1
        return count

    def count_emails(self):
        x = self.text
        email = re.findall(r"([a-z0-9+._-]+@[a-z0-9+._-]+\.[a-z0-9+_-]+\b)", x)
        return len(email)

    def count_urls(self):
        x = self.text
        urls = re.findall(r"(http|https|ftp|ssh)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", x)
        count = len(urls)
        return count

    def count_special_chars(self):
        x = self.text
        x = re.sub(r"[^\w ]+", "", x)
        return len(x)

    def count_phone_numbers(self):
        x = self.text
        phone = re.compile(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]")
        return len(re.findall(phone, x))

    def count_html_tags(self):
        x = self.text
        clean = re.compile("<.*?>")
        return len(re.findall(clean, x))

    def info(self):
        print(f"Length of String: {self.count_characters()}")
        print(f"Number of URLs: {self.count_urls()}")
        print(f"Number of Emails: {self.count_emails()}")
        print(f"Number of Words: {self.count_words()}")
        print(f"Average Word Count: {self.count_avg_wordlength()}")
        print(f"Number of Stopwords: {self.count_stopwords()}")
        print(f"Total Hashtags: {self.count_hashtags()}")
        print(f"Total Mentions: {self.count_mentions()}")
        print(f"Total Length of Numeric Data: {self.count_digits()}")
        print(f"Special Characters: {self.count_special_chars()}")
        print(f"White Spaces: {self.count_whitespace()}")
        print(f"Number of Vowels: {self.count_vowels()}")
        print(f"Number of Consonants: {self.count_consonants()}")
        print(f"Total Uppercase Words {self.count_uppercase_words()}")
        print(f"Number of Phone Number Inside Text: {self.count_phone_numbers()}")
        print(f"Number of HTML Tags {self.count_html_tags()}")
        print(f"Observed Sentiment: {Extractor(text=self.text).get_sentiment()}")


class Extractor(Counter):
    def __init__(self, text=None):
        super(Extractor, self).__init__()
        self.text = text

    def __str__(self):
        return f"{self.text}"

    def __repr__(self):
        return f'Extractor(text="{self.text}")'

    def get_stopwords(self):
        x = self.text.lower()
        lst = [text for text in x.split() if text in stopwords]
        return lst

    def get_sentence_tokens(self):
        return sent_tokenize(self.text)

    def get_word_tokens(self):
        return word_tokenize(self.text)

    def get_hashtags(self):
        x = self.text
        hashtags = [word for word in x.split() if word.startswith("#")]
        return hashtags

    def get_mentions(self):
        x = self.text
        mentions = [word for word in x.split() if word.startswith("@")]
        return mentions

    def get_digits(self):
        x = self.text
        digits = re.findall(r"[0-9]+", x)
        return digits

    def get_uppercase_words(self):
        x = self.text
        return [word for word in x.split() if word.isupper()]

    def get_emails(self):
        x = self.text
        emails = re.findall(r"([a-z0-9+._-]+@[a-z0-9+._-]+\.[a-z0-9+_-]+\b)", x)
        return emails

    def get_urls(self):
        x = self.text
        urls = re.findall(r"(http|https|ftp|ssh)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", x)
        return urls

    def get_repeated_words(self, n):
        x = self.text
        from collections import Counter

        x = x.split()
        frequent = Counter(x).most_common(n)
        return frequent

    def get_correct_spelling(self):
        x = self.text
        x = TextBlob(x).correct()
        return x

    def get_phone_numbers(self):
        x = self.text
        phone = re.compile(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]")
        return re.findall(phone, x)

    def get_html_tags(self):
        x = self.text
        clean = re.compile("<.*?>")
        return re.findall(clean, x)

    def get_sentiment(self):
        x = self.text
        score = TextBlob(x).sentiment.polarity
        if score == 0:
            sentiment = "Neutral"
        elif score < 0:
            sentiment = "Negative"
        elif score > 0:
            sentiment = "Positive"
        return score, sentiment


class Cleaner(Extractor):
    def __init__(self, text=None):
        super(Cleaner, self).__init__()
        self.text = text

    def __str__(self):
        return f"{self.text}"

    def __repr__(self):
        return f'Cleaner(text="{self.text}")'

    def remove_stopwords(self):
        x = self.text
        return " ".join([word for word in x.split() if word not in stopwords])

    def remove_digits(self):
        x = self.text
        return re.sub("[0-9]", "", x)

    def remomve_abber(self):
        abbreviations = json.load(open(abbreviations_path))
        x = self.text
        if type(x) is str:
            for key in abbreviations:
                value = abbreviations[key]
                x = x.replace(key, value)
            return x
        else:
            return x

    def remove_emails(self):
        x = self.text
        return re.sub(r"([a-z0-9+._-]+@[a-z0-9+._-]+\.[a-z0-9+_-]+)", "EMAIL", x)

    def remove_emails_c(self):
        x = self.text
        return re.sub(r"([a-z0-9+._-]+@[a-z0-9+._-]+\.[a-z0-9+_-]+)", "", x)

    def remove_urls(self):
        x = self.text
        return re.sub(
            r"(http|https|ftp|ssh)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", "URL ", x
        )

    def remove_urls_c(self):
        x = self.text
        return re.sub(r"(http|https|ftp|ssh)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", "", x)

    def remove_special_chars_c(self):
        x = self.text
        x = re.sub(r"[^\w ]+", "", x)
        x = " ".join(x.split())
        return x

    def remove_special_chars(self):
        x = self.text
        x = re.sub(r"[^\w ]+", "SpecialCharacter", x)
        x = " ".join(x.split())
        return x

    def remove_html_tags_c(self):
        x = self.text
        clean = re.compile("<.*?>")
        return re.sub(clean, "", x)

    def remove_html_tags(self):
        x = self.text
        clean = re.compile("<.*?>")
        return re.sub(clean, "HtmlTag", x)

    def remove_accented_chars(self):
        x = self.text
        x = unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode("utf-8", "ignore")
        return x

    def remove_emojis_c(self):
        emoj = re.compile(
            "["
            "\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\U0001f1e0-\U0001f1ff"
            "\U00002500-\U00002bef"
            "\U00002702-\U000027b0"
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2b55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"
            "\u3030"
            "]+",
            re.UNICODE,
        )
        x = self.text
        return re.sub(emoj, "", x)

    def remove_emojis(self):
        emoj = re.compile(
            "["
            "\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\U0001f1e0-\U0001f1ff"
            "\U00002500-\U00002bef"
            "\U00002702-\U000027b0"
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2b55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"
            "\u3030"
            "]+",
            re.UNICODE,
        )
        x = self.text
        return re.sub(emoj, "EMOJI", x)

    def remove_duplicate_words(self):
        x = self.text
        x = " ".join(set(x.split()))
        return x

    def remove_phone_numbers(self):
        x = self.text
        phone = re.compile(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]")
        return re.sub(phone, "PhoneNumber", x)

    def remove_phone_numbers_c(self):
        x = self.text
        phone = re.compile(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]")
        return re.sub(phone, "", x)

    def stemming(self):
        ps = PorterStemmer()
        text = " ".join([ps.stem(word) for word in word_tokenize(self.text)])
        return text

    def lemmatization(self):
        lemmatizer = WordNetLemmatizer()
        text = " ".join([lemmatizer.lemmatize(word) for word in word_tokenize(self.text)])
        return text

    def quick_clean(self, remove_complete, make_base):
        if remove_complete == True:
            self.text = self.remove_html_tags_c()
            self.text = self.remove_emails_c()
            self.text = self.remove_urls_c()
            self.text = self.remove_phone_numbers_c()
            self.text = self.remove_accented_chars()
            self.text = self.remove_emojis_c()
            self.text = self.remove_special_chars_c()
            self.text = self.remove_stopwords()
            self.text = self.remove_digits()
        else:
            self.text = self.remove_html_tags()
            self.text = self.remove_emails()
            self.text = self.remove_urls()
            self.text = self.remove_phone_numbers()
            self.text = self.remove_accented_chars()
            self.text = self.remove_emojis()
            self.text = self.remove_special_chars()
            self.text = self.remove_stopwords()
            self.text = self.remove_digits()
        if make_base == "stemming":
            self.text = self.stemming()
        elif make_base == "lemmatization":
            self.text = self.lemmatization()
        else:
            pass
        self.text = self.text.replace("  ", " ")
        self.text = " ".join(self.text.split())
        self.text = self.text.lower()
        return self.text


class Dataframe(Cleaner):
    def __init__(self, df=None, col=None):
        super(Dataframe, self).__init__()
        self.df = df
        self.col = col

    def __repr__(self):
        return f'Dataframe(df="{self.df}", col = "{self.col}")'

    def get_df_words_frequency_count(self):
        text = " ".join(self.df[self.col])
        text = text.split()
        freq = pd.Series(text).value_counts()
        return freq

    def clean(self, remove_complete, make_base):
        corpus = []
        for row in self.df[self.col]:
            doc = Cleaner(text=row)
            text = doc.quick_clean(remove_complete, make_base)
            corpus.append(text)
        return corpus


def _to_cv(corpus, max_features):
    cv = CountVectorizer(max_features=max_features)
    x = cv.fit_transform(corpus).toarray()
    return x, cv


def _to_tfidf(corpus, max_features):
    tfidf = TfidfVectorizer(max_features=max_features)
    x = tfidf.fit_transform(corpus).toarray()
    return x, tfidf
