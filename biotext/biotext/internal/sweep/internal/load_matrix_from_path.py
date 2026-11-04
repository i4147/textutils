import numpy as np
import h5py
import pickle
from scipy.io import loadmat


def load_matrix_from_path(path):
    errors = []

    try:
        return np.loadtxt(path, encoding="utf-8")
    except FileNotFoundError as e:
        raise FileNotFoundError(e)
    except Exception as e:
        errors.append(f"TXT load error: {e}")

    try:
        return np.load(path, allow_pickle=True)
    except Exception as e:
        errors.append(f"NPY load error: {e}")

    try:
        with h5py.File(path, "r") as file:
            first_key = list(file.keys())[0]
            return file[first_key][:]
    except Exception as e:
        errors.append(f"HDF5 load error: {e}")

    try:
        with h5py.File(path, "r") as file:
            first_key = list(file.keys())[0]
            return file[first_key][:]
    except OSError:
        try:
            mat_data = loadmat(path)
            keys = [key for key in mat_data.keys() if not key.startswith("__")]
            if len(keys) != 1:
                raise ValueError("The .mat file contains multiple datasets.")
            return mat_data[keys[0]]
        except Exception as e:
            errors.append(f"MAT load error: {e}")

    try:
        with open(path, "rb") as file:
            return pickle.load(file)
    except Exception as e:
        errors.append(f"Pickle load error: {e}")

    raise ValueError(f"Failed to load matrix from {path}. Errors:\n" + "\n".join(errors))
