from joblib import Parallel, delayed
from tqdm import tqdm
from .split_array import split_array


def parallelization(data_list, func, chunk_size=1000, n_jobs=1, desc=None, verbose=True):

    chunks = split_array(data_list, chunk_size)

    with tqdm(total=len(chunks), desc=desc, ncols=0, disable=not verbose) as progress_bar:
        result = Parallel(n_jobs=n_jobs, prefer="threads")(
            delayed(lambda chunk: (func(chunk), progress_bar.update()))(chunk) for chunk in chunks
        )

    result = [i[0] for i in result]

    result = [item for sublist in result for item in sublist]

    return result
