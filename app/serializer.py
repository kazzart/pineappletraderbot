import pickle
from typing import Any


def read_pickle(filename: str):
    with open(filename, "rb") as f:
        data = pickle.load(f)
        return data


def write_pickle(filename: str, data: Any):
    with open(filename, "wb") as f:
        pickle.dump(data, f)
