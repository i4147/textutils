from sklearn.feature_extraction.text import CountVectorizer
from textwiser.embeddings.tfidf import _ScikitEmbeddings


class _BOWEmbeddings(_ScikitEmbeddings):
    Model = CountVectorizer
