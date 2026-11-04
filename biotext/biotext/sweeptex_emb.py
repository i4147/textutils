import numpy as np
from typing import Optional, Union, List
from .sweeptex import sweeptex
from .internal import parallelization, tokenize, explode_list, count_occurrences, map_words_to_docs, map_docs_to_words


def sweeptex_emb(
    corpus: Union[List[str], np.ndarray],
    word_list: Optional[Union[List[str], np.ndarray]] = None,
    sweeped_corpus: Optional[List[np.ndarray]] = None,
    word_emb: Optional[np.ndarray] = None,
    return_doc_emb: bool = True,
    return_word_emb: bool = True,
    n_jobs: int = 1,
    chunk_size: int = 1000,
    verbose: bool = True,
) -> dict:

    if not isinstance(corpus, (list, np.ndarray)):
        raise TypeError(f"Input must be a list or a NumPy array. Received: {type(corpus).__name__}.")

    if word_list is not None and word_emb is not None:
        if len(word_list) != len(word_emb):
            raise ValueError(
                f"Dimension mismatch: word_list has {len(word_list)} words but word_emb has {len(word_emb)} vectors."
            )

    tokenize_par = lambda x: tokenize(x)
    tokenized_corpus = parallelization(
        corpus, tokenize_par, n_jobs=n_jobs, chunk_size=chunk_size, desc="Tokenizing texts", verbose=verbose
    )

    tokenized_corpus = [[word.strip("!@#$%^&*()[]{};:\"',<>?.") for word in sublist] for sublist in tokenized_corpus]

    if word_list is not None:
        if verbose:
            print("Using custom word list...")
        word_list = np.array(word_list)
        word_count = None
    else:
        if verbose:
            print("Creating vocabulary...")

        tokenized_corpus_set = [sorted(set(i)) for i in tokenized_corpus]

        tokenized_corpus_exp = explode_list(tokenized_corpus_set, return_indices=False)
        word_list, word_count = count_occurrences(tokenized_corpus_exp)
        word_list = np.array(word_list)
        word_count = np.array(word_count)

        sorted_indices = word_count.argsort(stable=True)[::-1]
        word_list = word_list[sorted_indices]
        word_count = word_count[sorted_indices]

        if word_emb is not None and len(word_emb) != len(word_list):
            raise ValueError(
                f"Pre-computed word embeddings dimension mismatch. Expected {len(word_list)}, got {len(word_emb)}."
            )

    sweeped_corpus = sweeped_corpus if sweeped_corpus is not None else sweeptex(corpus)

    word_to_idx = {item: index for index, item in enumerate(word_list)}

    output_dict = {"sweeped_corpus": sweeped_corpus, "word_list": word_list, "word_to_idx": word_to_idx}

    if word_list is None:
        output_dict["word_count"] = word_count

    if return_word_emb:
        if word_emb is None:
            word_doc_idx = map_words_to_docs(word_list, tokenized_corpus, verbose=verbose)

            word_emb_fun_par = lambda x: [
                np.mean(j, axis=0, where=~np.isnan(j)) for j in [sweeped_corpus[i] for i in x]
            ]
            word_emb = parallelization(
                word_doc_idx,
                word_emb_fun_par,
                n_jobs=n_jobs,
                chunk_size=chunk_size,
                desc="Creating word embedding",
                verbose=verbose,
            )
            word_emb = np.array(word_emb, dtype=np.float32)

        output_dict["word_emb"] = word_emb

    if return_doc_emb:
        doc_word_idx = map_docs_to_words(tokenized_corpus, word_list, verbose=verbose)

        doc_emb_fun_par = lambda x: [np.mean(j, axis=0, where=~np.isnan(j)) for j in [word_emb[i] for i in x]]
        doc_emb = parallelization(
            doc_word_idx,
            doc_emb_fun_par,
            n_jobs=n_jobs,
            chunk_size=chunk_size,
            desc="Creating document embedding",
            verbose=verbose,
        )
        doc_emb = np.array(doc_emb, dtype=np.float32)

        output_dict["doc_emb"] = doc_emb

    return output_dict
