# -*- coding: utf-8 -*-

from typing import Final

# https://github.com/cupy/cupy/blob/59e6c2b2e0c722b09c7a7af13f908942ef7806cc/cupy/cuda/memory.pyx#L805-L809
ALLOCATION_UNIT_SIZE: Final[int] = 512

# https://docs.nvidia.com/cuda/cuda-c-programming-guide/#interprocess-communication
IPC_ALLOCATION_UNIT_SIZE: Final[int] = 2 * 1024 * 1024
"""
Note that allocations made by cudaMalloc() may be sub-allocated from a larger block of
memory for performance reasons. In such case, CUDA IPC APIs will share the entire
underlying memory block which may cause other sub-allocations to be shared, which can
potentially lead to information disclosure between processes. To prevent this behavior,
it is recommended to only share allocations with a 2MiB aligned size.
"""


def align_malloc_size(size: int, alignment: int) -> int:
    if size <= 0:
        raise ValueError("'size' must be positive")
    if alignment <= 0:
        raise ValueError("'alignment' must be positive")

    if size % alignment == 0:
        return size
    else:
        return ((size // alignment) + 1) * alignment


def align_ipc_malloc_size(size: int) -> int:
    return align_malloc_size(size, IPC_ALLOCATION_UNIT_SIZE)
