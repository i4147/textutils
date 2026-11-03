def gen(text):
    import re

    tweet = text
    tweet = re.sub(r"(\\u[0-9A-Fa-f]+)", r"", tweet)
    tweet = re.sub(r"[^\x00-\x7f]", r"", tweet)
    tweet = re.sub("((www\.[^\s]+)|(https?://[^\s]+))", "", tweet)
    tweet = re.sub("@[^\s]+", "", tweet)
    tweet = re.sub("[\s]+", " ", tweet)
    tweet = re.sub("[\n]+", " ", tweet)
    tweet = re.sub(r"[^\w]", " ", tweet)
    tweet = re.sub(r"#([^\s]+)", r"\1", tweet)
    tweet = re.sub(r"#([^\s]+)", r"\1", tweet)
    tweet = tweet.replace(":)", "")
    tweet = tweet.replace(":(", "")
    tweet = re.sub(r"(\!)\1+", " ", tweet)
    tweet = re.sub(r"(\?)\1+", " ", tweet)
    tweet = re.sub(r"(\.)\1+", " ", tweet)
    tweet = re.sub(r"[^\w\s]", "", tweet)
    tweet = tweet.strip("'\"")
    return tweet


def stopw(text, ext=[]):
    from nltk.corpus import stopwords

    tweet = text
    stop = stopwords.words("english") + ext
    tweet = " ".join([x for x in tweet.split() if x.lower() not in stop])
    return tweet


def lemma(text):
    tweet = text
    from textblob import Word

    tweet = " ".join([Word(word).lemmatize() for word in tweet.split()])
    return tweet


def stem(text):
    from nltk.stem import PorterStemmer

    tweet = text
    st = PorterStemmer()
    tweet = " ".join([st.stem(word) for word in tweet.split()])
    return tweet


def low(text):
    tweet = text
    tweet = tweet.lower()
    return tweet


def dig(text):
    tweet = text
    tweet = "".join([i for i in tweet if not i.isdigit()])
    return tweet


def clean_len(text):
    tweet = text
    tweet = " ".join([i for i in tweet.split() if len(i) > 2])
    return tweet


def spell(text):
    from textblob import TextBlob

    tweet = text
    return str(TextBlob(text).correct())


def countvec(df):
    import pandas as pd
    from sklearn.feature_extraction.text import CountVectorizer

    if type(df) == list:
        cv = CountVectorizer()
        count_vector = cv.fit_transform(df)
        return (
            count_vector,
            cv.get_feature_names(),
            pd.DataFrame(count_vector.toarray(), columns=cv.get_feature_names()),
        )
    else:
        df1 = list(df.iloc[:, 0])
        cv = CountVectorizer()
        count_vector = cv.fit_transform(df1)
        return (
            count_vector,
            cv.get_feature_names(),
            pd.DataFrame(count_vector.toarray(), columns=cv.get_feature_names()),
        )


def tfidf(df):
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer

    if type(df) == list:
        tfidf = TfidfVectorizer()
        tfidf_vector = tfidf.fit_transform(df)
        return (
            tfidf_vector,
            tfidf.get_feature_names(),
            pd.DataFrame(tfidf_vector.toarray(), columns=tfidf.get_feature_names()),
        )
    else:
        df1 = list(df.iloc[:, 0])
        tfidf = TfidfVectorizer()
        tfidf_vector = tfidf.fit_transform(df1)
        return (
            tfidf_vector,
            tfidf.get_feature_names(),
            pd.DataFrame(tfidf_vector.toarray(), columns=tfidf.get_feature_names()),
        )


def WCloud(process):
    allWords = " ".join([twts for twts in process])
    import nltk
    from nltk.corpus import webtext
    from nltk.probability import FreqDist
    import string

    allWords_words = allWords.split()
    len(allWords_words)
    frequency_dist = nltk.FreqDist(allWords_words)
    print(frequency_dist)
    sorted_frequency_dist = sorted(frequency_dist, key=frequency_dist.__getitem__, reverse=True)
    sorted_frequency_dist
    large_words = dict([(k, v) for k, v in frequency_dist.items() if len(k) > 3])
    frequency_dist = nltk.FreqDist(large_words)
    frequency_dist.plot(50, cumulative=False)
    from wordcloud import WordCloud

    wcloud = WordCloud().generate_from_frequencies(frequency_dist)
    import matplotlib.pyplot as plt

    plt.imshow(wcloud, interpolation="bilinear")
    plt.axis("off")
    (-0.5, 399.5, 199.5, -0.5)
    plt.show
