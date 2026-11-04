# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.linear_model import SGDClassifier
from sklearn.svm import LinearSVC
from scipy import sparse
import pandas as pd
import numpy as np
import os
import warnings


class TextClassifier:
    def __init__(self, texts, ids, vocabulary=None, encoding="utf-8"):
        this_dir, this_filename = os.path.split(__file__)
        es_stopwords = pd.read_csv(os.path.join(this_dir, "ES_stopwords.txt"), header=None, encoding="utf-8")
        es_stopwords = list(np.squeeze(es_stopwords.values))
        self._check_id_length(ids)
        self.vectorizer = CountVectorizer(
            input="content",
            encoding=encoding,
            decode_error="strict",
            strip_accents="ascii",
            lowercase=True,
            preprocessor=None,
            tokenizer=None,
            stop_words=es_stopwords,
            ngram_range=(1, 1),
            analyzer="word",
            max_df=1.0,
            min_df=1,
            max_features=None,
            vocabulary=vocabulary,
            binary=False,
        )

        self.transformer = TfidfTransformer()
        self.ids = None
        self.term_mat = None
        self.tfidf_mat = None
        self.reload_texts(texts, ids)

    def __str__(self):
        string = """ Clasificador de textos con {:d} textos almacenados, \
        """.format(len(self.ids))
        return string

    def make_classifier(self, name, ids, labels):
        if not all(np.in1d(ids, self.ids)):
            raise ValueError(
                "Hay ids de textos que no se encuentran \
                              almacenados."
            )
        setattr(self, name, SGDClassifier())
        classifier = getattr(self, name)
        indices = np.searchsorted(self.ids, ids)
        classifier.fit(self.tfidf_mat[indices, :], labels)

    def retrain(self, name, ids, labels):
        if not all(np.in1d(ids, self.ids)):
            raise ValueError(
                "Hay ids de textos que no se encuentran \
                              almacenados."
            )
        try:
            classifier = getattr(self, name)
        except AttributeError:
            raise AttributeError("No hay ningun clasificador con ese nombre.")
        indices = np.in1d(self.ids, ids)
        if isinstance(labels, basestring):
            labels = [labels]
        classifier.partial_fit(self.tfidf_mat[indices, :], labels)

    def classify(self, classifier_name, examples, max_labels=None, goodness_of_fit=False):
        classifier = getattr(self, classifier_name)
        texts_vectors = self._make_text_vectors(examples)
        return classifier.classes_, classifier.decision_function(texts_vectors)

    def _make_text_vectors(self, examples):
        if isinstance(examples, basestring):
            if examples in self.ids:
                textvec = self.tfidf_mat[self.ids == examples, :]
            else:
                textvec = self.vectorizer.transform([examples])
                textvec = self.transformer.transform(textvec)
        elif type(examples) is list:
            if all(np.in1d(examples, self.ids)):
                textvec = self.tfidf_mat[np.in1d(self.ids, examples)]
            elif not any(np.in1d(examples, self.ids)):
                textvec = self.vectorizer.transform(examples)
                textvec = self.transformer.transform(textvec)
            else:
                raise ValueError(
                    "Las listas de ejemplos deben ser todos ids\
                                  de textos almacenados o todos textos planos"
                )
        else:
            raise TypeError("Los ejemplos no son del tipo de dato adecuado.")
        return textvec

    def get_similar(self, example, max_similars=3, similarity_cutoff=None, term_diff_cutoff=0.6):
        if max_similars > self.term_mat.shape[0]:
            raise ValueError(
                "No se pueden pedir mas sugerencias que la \
                              cantidad de textos que hay almacenados."
            )
        if example in self.ids:
            index = self.ids == example
            exmpl_vec = self.tfidf_mat[index, :]
            distances = np.squeeze(pairwise_distances(self.tfidf_mat, exmpl_vec))
            distances[index] = np.inf
        else:
            exmpl_vec = self.vectorizer.transform([example])
            exmpl_vec = self.transformer.transform(exmpl_vec)
            distances = np.squeeze(pairwise_distances(self.tfidf_mat, exmpl_vec))
        sorted_indices = np.argsort(distances)
        closest_n = sorted_indices[:max_similars]
        sorted_dist = distances[closest_n]
        if similarity_cutoff:
            closest_n = closest_n[sorted_dist < similarity_cutoff]
            sorted_dist = sorted_dist[sorted_dist < similarity_cutoff]
        best_words = []
        exmpl_vec = exmpl_vec.toarray()
        for suggested in closest_n:
            test_vec = self.tfidf_mat[suggested, :].toarray()
            differences = np.abs(exmpl_vec - test_vec) ** 2 / (exmpl_vec**2 + test_vec**2)
            differences = np.squeeze(np.array(differences))
            sort_I = np.argsort(differences)
            limit = np.flatnonzero((differences[sort_I] > term_diff_cutoff) | (np.isnan(differences[sort_I])))[0]
            best_words.append([k for k, v in self.vectorizer.vocabulary_.iteritems() if v in sort_I[:limit]])
        text_ids = self.ids[closest_n]
        return list(text_ids), list(sorted_dist), best_words

    def reload_texts(self, texts, ids, vocabulary=None):
        self._check_id_length(ids)
        self.ids = np.array(sorted(ids))
        if vocabulary:
            self.vectorizer.vocabulary = vocabulary
        sorted_texts = [x for (y, x) in sorted(zip(ids, texts))]
        self.term_mat = self.vectorizer.fit_transform(sorted_texts)
        self._update_tfidf()

    # def store_text(self, texts, ids, replace_texts=False):
    #     """Calcula los vectores de terminos de un texto y los almacena.
    #         NOT IMPLEMENTED.
    #     Nota:
    #         Esta funcion usa el vocabulario que ya esta almacenado, es decir,
    #         que no se incorporan nuevos terminos. Si se quiere cambiar el
    #         vocabulario deben recargarse todos los textos con
    #         :func:`~TextClassifier.TextClassifier.reload_texts`
    #     Args:
    #         texts (list): Una lista de N textos a incorporar.
    #         ids (list of str): Una lista de N ids alfanumericos para los textos
    #         replace_texts (bool, optional): Indica si deben reemplazarse los
    #             textos cuyo id ya este almacenado. Si es False y algun id ya se
    #             encuentra almacenado se considera un error.
    #     """
    #     self._check_id_length(ids)
    #     if not replace_texts and any(np.in1d(ids, self.ids)):
    #         raise ValueError("Alguno de los ids provistos ya esta en el \
    #                           indice")
    #     else:
    #         ids = np.array(ids)
    #         partial_mat = self.vectorizer.transform(texts)
    #         # Si no hay ids ya guardados solo concateno y los agrego al
    #         # array self.ids
    #         if not any(np.in1d(ids, self.ids)):
    #             self.ids = np.r_[self.ids, ids]
    #             self.term_mat = sparse.vstack((self.term_mat,
    #                                            partial_mat))
    #         # Si los hay,
    #         else:
    #             oldrows = np.in1d(self.ids, ids)
    #             oldpartial = np.in1d(ids, self.ids)
    #             # Actualizo las filas que ya estaban
    #             self.term_mat[oldrows, :] = partial_mat[oldpartial, :]
    #             # y agrego las que no
    #             partial_mat = partial_mat[~oldpartial, :]
    #             self.term_mat = sparse.vstack((self.term_mat, partial_mat))
    #             # concateno los viejos ids y los nuevos
    #             self.ids = np.r_[self.ids, ids[~oldpartial]]
    #     self._update_tfidf()

    def _update_tfidf(self):
        self.tfidf_mat = self.transformer.fit_transform(self.term_mat)

    def _check_id_length(self, ids):
        if any(map(lambda x: len(x) > 10, ids)):
            warnings.warn(
                "Hay ids que son muy largos. Es posible que se hayan \
            ingresado textos planos en lugar de ids."
            )

    def _check_repeated_ids(self, ids):
        if length(np.unique(ids)) != length(ids):
            raise ValueError("Hay ids repetidos.")
