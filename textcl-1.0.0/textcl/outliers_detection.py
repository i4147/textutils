from __future__ import division, print_function
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import preprocessing
import nltk
from nltk.corpus import stopwords
from scipy import stats


class _R_pca:
    def __init__(self, D, mu=None, lmbda=None):
        self.D = D
        self.S = np.zeros(self.D.shape)
        self.Y = np.zeros(self.D.shape)
        if mu:
            self.mu = mu
        else:
            self.mu = np.prod(self.D.shape) / (4 * np.linalg.norm(self.D, ord=1))
        self.mu_inv = 1 / self.mu
        if lmbda:
            self.lmbda = lmbda
        else:
            self.lmbda = 1 / np.sqrt(np.max(self.D.shape))

    @staticmethod
    def frobenius_norm(M):
        return np.linalg.norm(M, ord="fro")

    @staticmethod
    def shrink(M, tau):
        return np.sign(M) * np.maximum((np.abs(M) - tau), np.zeros(M.shape))

    def svd_threshold(self, M, tau):
        U, S, V = np.linalg.svd(M, full_matrices=False)
        return np.dot(U, np.dot(np.diag(self.shrink(S, tau)), V))

    def fit(self, tol=None, max_iter=1000, iter_print=100):
        iter = 0
        err = np.Inf
        Sk = self.S
        Yk = self.Y
        Lk = np.zeros(self.D.shape)
        if tol:
            _tol = tol
        else:
            _tol = 1e-7 * self.frobenius_norm(self.D)
        while (err > _tol) and iter < max_iter:
            Lk = self.svd_threshold(self.D - Sk + self.mu_inv * Yk, self.mu_inv)
            Sk = self.shrink(self.D - Lk + (self.mu_inv * Yk), self.mu_inv * self.lmbda)
            Yk = Yk + self.mu * (self.D - Lk - Sk)
            err = self.frobenius_norm(self.D - Lk - Sk)
            iter += 1
        self.L = Lk
        self.S = Sk
        return Lk, Sk


def rpca_implementation(bag_of_words):
    rpca = _R_pca(np.array(bag_of_words))
    _, outlier_matrix = rpca.fit(max_iter=10000, iter_print=100)
    return outlier_matrix


def tonmf(A, k, alpha, beta):
    m, n = A.shape
    numIterationsWH = 10
    numIterations = 10
    W = np.random.random((m, k)).reshape([k, m]).T
    H = np.random.random((k, n)).reshape([n, k]).T
    D = A - np.dot(W, H)
    currentIteration = 1
    Z = np.zeros((m, n))
    prevErr = np.linalg.norm(D, ord="fro") + beta * np.linalg.norm(H, ord=1)
    currentErr = prevErr - 1
    errChange = np.zeros((numIterations + 1, 1))
    while currentIteration < numIterations:
        colnormdi = np.sqrt(np.sum(np.square(D), axis=0))
        colnormdi_factor = colnormdi - alpha
        colnormdi_factor[colnormdi_factor < 0] = 0
        Z = np.divide(D, colnormdi)
        Z = np.array(Z) * np.array(colnormdi_factor)
        D = A - Z
        W, H, _ = _hals(D, W, H, k, 1e-6, numIterationsWH, beta)
        D = A - np.dot(W, H)
        if currentIteration > 1:
            prevErr = currentErr
        errChange[currentIteration] = prevErr
        currentErr = (
            np.linalg.norm(D - Z, ord="fro")
            + alpha * np.sum(np.sqrt(np.sum(np.square(Z))))
            + beta * np.linalg.norm(H, ord=1)
        )
        currentIteration = currentIteration + 1
    errChange[currentIteration] = currentErr
    return Z, W, H, errChange


def _hals(A, Winit, Hinit, k, tolerance, numIterations, beta):
    W = Winit
    H = Hinit
    prevError = np.linalg.norm(A - np.dot(W, H), ord="fro")
    currError = prevError + 1
    currentIteration = 1
    errChange = np.zeros((1, numIterations + 1))[0]
    while abs(currError - prevError) > tolerance and currentIteration < numIterations:
        AHt = np.dot(A, np.transpose(H))
        HHt = np.dot(H, np.transpose(H))
        HHtDiag = np.array(np.diag(HHt))
        HHtDiag[HHtDiag == 0] = np.finfo(float).eps
        for x in range(0, k, 1):
            Wx = W[:, x] + (np.array(np.transpose(AHt[:, x]))[0] - np.dot(W, HHt[:, x])) / HHtDiag[x]
            Wx[Wx < np.finfo(float).eps] = np.finfo(float).eps
            W[:, x] = Wx
        WtA = np.dot(np.transpose(W), A)
        WtW = np.dot(np.transpose(W), W)
        WtWDiag = np.array(np.diag(WtW))
        WtWDiag[WtWDiag == 0] = np.finfo(float).eps
        for x in range(0, k, 1):
            Hx = H[x, :] + (np.array(WtA[x, :]) - np.dot(WtW[x, :], H)) / WtWDiag[x]
            Hx = Hx - beta / WtWDiag[x]
            Hx[Hx < np.finfo(float).eps] = np.finfo(float).eps
            H[x, :] = Hx
        if currentIteration > 1:
            prevError = currError
        errChange[currentIteration] = prevError
        currError = np.linalg.norm(A - np.dot(W, H), ord="fro")
        currentIteration = currentIteration + 1
    return W, H, errChange


def svd(bag_of_words):
    _, S, V = np.linalg.svd(bag_of_words, full_matrices=False)
    outlier_matrix = np.dot(np.sqrt(np.diag(S)), V)
    return outlier_matrix


def outlier_detection(
    split_search_results_df,
    method="tonmf",
    norm="l2",
    stop_words_lang="english",
    Z_threshold=3,
    label_col="topic_name",
    text_col="text",
    k=10,
    alpha=10,
    beta=0.05,
):
    nltk.download("stopwords")
    stop = stopwords.words(stop_words_lang)
    split_search_results_df["words"] = split_search_results_df[text_col].apply(
        lambda x: " ".join([word for word in x.split() if word.lower() not in stop])
    )
    for topic in split_search_results_df[label_col].unique():
        bag_of_words = (
            CountVectorizer()
            .fit_transform(split_search_results_df[split_search_results_df[label_col] == topic]["words"])
            .todense()
        )
        if method == "rpca":
            outlier_matrix = rpca_implementation(bag_of_words)
        elif method == "tonmf":
            outlier_matrix, _, _, _ = tonmf(bag_of_words, k, alpha, beta)
        elif method == "svd":
            outlier_matrix = svd(bag_of_words.T)
            outlier_matrix = outlier_matrix.T
        else:
            raise Exception('method should be in list ["tonmf", "rpca", "svd"]')
        if norm == "l2" or norm == "l1" or norm == "max":
            _, y_pred = preprocessing.normalize(outlier_matrix, axis=1, norm=norm, return_norm=True)
        else:
            raise Exception('norm should be in list ["l1", "l2", "max"]')
        Z = stats.zscore(y_pred)
        split_search_results_df.loc[(split_search_results_df[label_col] == topic), "Z_score"] = np.abs(Z)
    split_search_results_df["Z_score"] = split_search_results_df["Z_score"].fillna(0)
    return split_search_results_df[split_search_results_df["Z_score"] <= Z_threshold], split_search_results_df[
        split_search_results_df["Z_score"] > Z_threshold
    ]
