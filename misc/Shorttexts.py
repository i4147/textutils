import json
import random
import numpy as np
import jieba
from sklearn.externals import joblib
from sklearn.linear_model import LogisticRegression
import re


def user_vector(q):
    import synonyms

    user_input = q
    user_senstence = re.sub(
        "[\u3002\uff1f\uff01\uff0c\u3001|\uff1b\uff1a\u201c\u201d\u2018\u2019\uff08\uff09\u300a\u300b\u3008\u3009\u3010\u3011\u300e\u300f\u300c\u300d\ufe43\ufe44\u3014\u3015\u2026\u2014\uff5e\ufe4f\uffe5]",
        "",
        user_input,
    )
    user_vectors = []
    users_vector = np.zeros((100,))
    cut_user = jieba.lcut(user_senstence)
    for cut_word in cut_user:
        try:
            word_vector = synonyms.v(cut_word)
            users_vector += word_vector
        except:
            pass
    user_vectors.append(users_vector)
    user_vectors = np.array(user_vectors)
    return user_vectors


def shorttext_result(q):
    dict_title = {}
    user_vectors = user_vector(q)
    clf2 = joblib.load("regressor.pkl")
    result = clf2.predict(user_vectors)
    result = str(result[0])
    dict_title["title_type"] = result
    return dict_title
