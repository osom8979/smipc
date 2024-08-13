# -*- coding: utf-8 -*-

import platform
import sys
from functools import lru_cache
from typing import Tuple

# https://docs.nvidia.com/cuda/cuda-c-programming-guide/#interprocess-communication
IPC_COMPUTE_CAPABILITY_VERSION: Tuple[int, int] = 2, 0
"""
The IPC API is only supported for 64-bit processes on Linux and for devices of
compute capability 2.0 and higher.
"""


class CompatibleError(RuntimeError):
    pass


@lru_cache
def has_cupy() -> bool:
    try:
        import cupy  # noqa
    except ImportError:
        return False
    else:
        return True


@lru_cache
def has_torch() -> bool:
    try:
        import torch  # noqa
    except ImportError:
        return False
    else:
        return True


@lru_cache
def compatible_ipc() -> bool:
    if platform.system().lower() != "linux":
        raise CompatibleError("The application only supported on Linux OS.")

    # https://docs.python.org/3/library/platform.html#platform.architecture
    if sys.maxsize <= 2**32:
        raise CompatibleError("The application must be built as a 64-bit target.")

    kernel_version_text = platform.release()  # e.g. "5.15.0-107-generic"
    kernel_semver = tuple(int(v) for v in kernel_version_text.split("-")[0].split("."))

    # https://github.com/ndd314/cuda_examples/blob/master/0_Simple/simpleIPC/simpleIPC.cu
    if kernel_semver < (2, 6, 18):
        raise CompatibleError(
            "IPC is only supported with Linux OS kernel version 2.6.18 and higher"
        )

    if not has_cupy():
        raise CompatibleError("The cupy package is required")

    # noinspection PyUnresolvedReferences
    import cupy

    num_devices = cupy.cuda.runtime.getDeviceCount()
    if num_devices <= 0:
        raise CompatibleError("CUDA device not found")

    for i in range(num_devices):
        props = cupy.cuda.runtime.getDeviceProperties(i)
        assert isinstance(props, dict)

        compute_capability = props["major"], props["minor"]
        if compute_capability < IPC_COMPUTE_CAPABILITY_VERSION:
            raise CompatibleError(
                f"Computing capability must be 2.0 or higher in Device({i})"
            )

        device_overlap = props["deviceOverlap"]
        if not device_overlap:
            raise CompatibleError(f"Unsupported deviceOverlap in Device({i})")

    return True
