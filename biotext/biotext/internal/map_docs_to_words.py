from tqdm import tqdm


def map_docs_to_words(tokenized_docs, word_list, verbose=True):
    word_dict = {token: i for i, token in enumerate(word_list)}

    word_keys = set(word_dict.keys())

    doc_word_idx = []

    for doc in tqdm(tokenized_docs, desc="Searching", ncols=0, disable=not verbose):
        doc_word_idx.append([word_dict[token] for token in doc if token in word_keys])

    return doc_word_idx
