import numpy as np
from .internal import create_seqrecord_list, parallelization, sweep
from .aminocode import aminocode


def sweeptex(corpus, emb_size=1200, n_jobs=1, chunk_size=1000, verbose=True):

    if verbose:
        print("Starting SWeeP...")

    if not isinstance(corpus, (list, np.ndarray)):
        raise TypeError(f"Input must be a list or a NumPy array. Received: {type(corpus).__name__}.")

    if emb_size % 4 != 0:
        raise ValueError(f"proj_size ({emb_size}) must be divisible by 4.")

    par_function = lambda x: aminocode.encode_list(x)
    encoded_corpus = parallelization(
        corpus, par_function, n_jobs=n_jobs, chunk_size=chunk_size, desc="Encoding", verbose=verbose
    )

    mask = [[1, 1, 0, 0, 1], [1, 1, 1, 0, 0], [1, 0, 1, 0, 1], [1, 1, 0, 1, 0]]
    proj_size = int(emb_size / 4)

    ntake = sum(mask[0])
    proj = sweep.create_proj_mat(20**ntake, proj_size)

    encoded_corpus_fasta = create_seqrecord_list(encoded_corpus)
    sweeped_corpus = sweep.fasta_to_sweep(
        encoded_corpus_fasta,
        proj=proj,
        mask=mask,
        n_jobs=n_jobs,
        chunk_size=chunk_size,
        print_details=False,
        progress_bar=verbose,
    )

    if verbose:
        print("SWeeP completed.")

    return sweeped_corpus
