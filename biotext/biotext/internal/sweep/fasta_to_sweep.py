import numpy as np
from time import time
from tqdm import tqdm
import warnings
import math
from joblib import Parallel, delayed
import sys

from .utils import fastaread, orthrand, create_sweep_masks
from .internal import aa_to_num, count_occ, load_matrix_from_path, nt_to_num, scan_mask, transform_with_lambert_w


def fasta_to_sweep(
    fasta,
    proj=1369,
    seq_type="aa",
    mask=None,
    xbinary=False,
    minus_one_mode=False,
    supress_proj=False,
    stack_result=True,
    n_jobs=1,
    chunk_size=1000,
    progress_bar=True,
    print_details=True,
):

    start_t = time()

    if isinstance(fasta, str):
        fasta = fastaread(fasta)
    try:
        seq = [str(i.seq).upper() for i in fasta]
    except AttributeError:
        seq = [i.upper() for i in fasta]

    if mask is None or len(mask) == 0:
        mask = create_sweep_masks(6, 4)
    elif type(mask[0]) == int:
        mask = [mask]

    nmask = len(mask)

    R_idx = []
    ldv_len = None
    if isinstance(proj, str):
        R = [load_matrix_from_path(proj)]
        R_idx = [0] * nmask
        ldv_len = [len(R[0])] * nmask
        proj_type = "single_file"
    elif isinstance(proj, (np.ndarray, list)):
        if isinstance(proj, list):
            if all(isinstance(item, str) for item in proj):
                R = [load_matrix_from_path(path) for path in proj]
                proj_type = "list_of_files"
            elif all(isinstance(item, np.ndarray) for item in proj):
                R = proj
                proj_type = "list_of_matrices"
            elif all(isinstance(item, int) for item in proj):
                R = []
                R_idx = [0] * nmask
                ldv_len = proj
                proj_type = "list_of_projection_sizes"
        else:
            R = [np.array(proj)]
            proj_type = "matrix"
        ldv_len = [len(i[0]) for i in R] if not isinstance(ldv_len, list) else ldv_len
        if len(R) > 1:
            R_idx = list(range(0, nmask))
        else:
            R_idx = [0] * nmask
            if proj_type != "list_of_projection_sizes":
                ldv_len = ldv_len * nmask
    elif isinstance(proj, int):
        R = []
        R_idx = [0] * nmask
        ldv_len = [proj] * nmask
        proj_type = "projection_size"
        if minus_one_mode:
            warnings.warn(
                ("Warning: 'minus_one_mode' has no effect when 'proj' is an integer (projection size)."), UserWarning
            )
    else:
        raise ValueError(
            "proj must be an integer, numpy.ndarray, list of lists or numpy "
            "arrays, a single path (str), or a list of paths to matrix files."
        )

    if len(ldv_len) > nmask:
        warnings.warn((f"Warning: There are more projection sizes ({len(ldv_len)}) than masks ({nmask})."), UserWarning)
    elif len(ldv_len) < nmask:
        raise ValueError(f"Error: There are fewer projection sizes ({len(ldv_len)}) than masks ({nmask}).")

    if seq_type == "aa":
        seq_to_num = aa_to_num
        seq_type_len = 20
    elif seq_type == "nt":
        seq_to_num = nt_to_num
        seq_type_len = 4

    morthrand = len(R) == 0

    ntake, nbits, hdv_len, Um, Un, xnorm = [], [], [], [], [], []
    for i in range(0, nmask):
        m = mask[i]
        ntake.append(sum(m))
        nbits.append(len(m))
        hdv_len.append(seq_type_len ** ntake[i])

        if morthrand:
            Um.append(np.sin(range(1, ldv_len[i] + 1)))
            Un.append(np.sin(range(1, hdv_len[i] + 1)))
            xnorm.append(np.sqrt(hdv_len[i] / 3))

    if proj_type not in ("projection_size", "list_of_projection_sizes"):
        ntake_uni_len = len(set(ntake))
        if ntake_uni_len != 1 and len(R) == 1:
            raise ValueError(
                "When masks have values different from 'ntake', and a "
                "precomputed projection matrix is desired as input, 'proj' "
                "must be a list containing one matrix for each mask."
            )
        R_shape_error = []
        for i in range(nmask):
            R_shape = np.shape(R[R_idx[i]])
            if R_shape[0] != hdv_len[i]:
                R_shape_error.append(i)
        if R_shape_error:
            raise ValueError(
                "The masks at the following indices are incompatible with the "
                f"corresponding projection matrix: {R_shape_error}. "
                f"The number of rows must be {seq_type_len}**ntake (where "
                "ntake is the number of take positions in the mask), "
                f"resulting in {seq_type_len}**ntake rows for each projection "
                "matrix."
            )
    if xbinary:
        fx = lambda x: (x > 0) + 0
    else:
        fx = lambda x: transform_with_lambert_w(x)

    nfas = len(seq)

    if print_details:
        print(f"Number of sequences: {nfas}")
        print(f"Number of masks: {nmask}")
        print(f"nbits: {', '.join(map(str, nbits))}")
        print(f"ntake: {', '.join(map(str, ntake))}")
        print(f"Masks: {', '.join(f'{row}' for row in mask)}")
        print(f"HDV length: {', '.join(map(str, hdv_len))}")
        if not supress_proj:
            print(f"LDV length: {', '.join(map(str, ldv_len))}")
        print(f"Projection input type: {proj_type.replace('_', ' ')}")

    chunks = math.ceil(nfas / chunk_size)
    range_s = range(0, chunks)
    chunk_indices = np.tile(chunk_size, (chunks, 2)) * np.array([
        list(range(0, chunks)),
        list(range(1, chunks + 1)),
    ]).T + np.concatenate((np.ones((chunks, 1)), np.zeros((chunks, 1))), axis=1)
    chunk_indices[-1, 1] = nfas
    chunk_indices = chunk_indices - 1

    def sweep_chunk(i, progress_bar):
        CT_expanded_list = [[] for _ in range(nmask)]

        if supress_proj:
            HDV_chunk = [[] for _ in range(nmask)]
        SWP_chunk = [[] for _ in range(nmask)]

        seq_chunk = seq[int(chunk_indices[i, 0]) : int(chunk_indices[i, 1]) + 1]
        seq_chunk_len = len(seq_chunk)

        for k in range(seq_chunk_len):
            s = seq_chunk[k]

            for j in range(nmask):
                SSlist = scan_mask(s, mask[j])
                HDV = seq_to_num(SSlist)
                HDV = [x for x in HDV if 0 <= x < hdv_len[j]]
                CT = list(count_occ(HDV))
                CT[1] = fx(np.array(CT[1]))

                if supress_proj:
                    hdv_vec = np.zeros(hdv_len[j])
                    if minus_one_mode:
                        hdv_vec -= 1
                    hdv_vec[CT[0]] = CT[1]
                    HDV_chunk[j].append(hdv_vec)
                else:
                    if morthrand:
                        swp = CT[1].reshape(1, -1) @ ((1 / xnorm[j]) * orthrand(CT[0], Um[j], Un[j]))
                        SWP_chunk[j].append(swp)

                    else:
                        CT_expanded = np.zeros((1, hdv_len[j]))
                        if minus_one_mode:
                            CT_expanded -= 1
                        CT_expanded[:, CT[0]] = CT[1]
                        CT_expanded_list[j].append(CT_expanded)

            progress_bar.update(1)

        for j in range(nmask):
            if supress_proj:
                SWP_chunk[j] = np.vstack(HDV_chunk[j])
            elif not morthrand:
                CT_expanded_list[j] = np.vstack(CT_expanded_list[j])
                swp = CT_expanded_list[j] @ R[R_idx[j]]
                SWP_chunk[j] = swp
            else:
                SWP_chunk[j] = np.vstack(SWP_chunk[j])

        return SWP_chunk

    total_sequences = len(seq)
    with tqdm(
        total=total_sequences, desc="Processing sequences", file=sys.stdout, ncols=0, disable=(not progress_bar)
    ) as progress_bar:
        SWP = Parallel(n_jobs=n_jobs, prefer="threads")(delayed(sweep_chunk)(i, progress_bar) for i in range_s)
    SWP = [np.vstack(i) for i in zip(*SWP)]

    end_t = time()
    if print_details:
        print("Elapsed time:", end_t - start_t)

    if stack_result:
        SWP = np.hstack(SWP)

    return SWP
