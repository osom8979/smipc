# -*- coding: utf-8 -*-

from typing import Any, Dict, Final

import numpy as np

_DTYPE_TO_INDEX: Final[Dict[Any, int]] = {
    # --------------------
    np.uint8: 8,
    np.uint16: 16,
    np.uint32: 32,
    np.uint64: 64,
    # np.uint128: 128,
    # np.uint256: 256,
    # --------------------
    np.int8: 1008,
    np.int16: 1016,
    np.int32: 1032,
    np.int64: 1064,
    # np.int128: 1128,
    # np.int256: 1256,
    # --------------------
    np.float16: 2016,
    np.float32: 2032,
    np.float64: 2064,
    # np.float80: 2080,
    # np.float96: 2096,
    # np.float128: 2128,
    # np.float256: 2256,
    # --------------------
    # np.complex64: 3064,
    # np.complex128: 3128,
    # np.complex160: 3160,
    # np.complex192: 3192,
    # np.complex256: 3256,
    # np.complex512: 3512,
    # --------------------
}

_INDEX_TO_DTYPE: Final[Dict[int, Any]] = {v: k for k, v in _DTYPE_TO_INDEX.items()}


def serialize_dtype(dtype):
    return _DTYPE_TO_INDEX[dtype]


def deserialize_dtype(index):
    return _INDEX_TO_DTYPE[index]
