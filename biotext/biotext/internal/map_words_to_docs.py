from tqdm import tqdm
from collections import defaultdict


def map_words_to_docs(word_list, tokenized_docs, verbose=True):
    word_set = set(word_list)

    tokenized_docs = [set(doc) for doc in tokenized_docs]

    token_idx = defaultdict(list)

    for index, doc in enumerate(tqdm(tokenized_docs, desc="Searching", ncols=0, disable=not verbose)):
        for token in doc:
            if token in word_set:
                token_idx[token].append(index)

    return [token_idx[token] for token in word_list]
