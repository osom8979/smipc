# -*- coding: utf-8 -*-

from typing import Optional

import numpy

try:
    import cupy  # noqa
except ImportError:
    pass

try:
    import torch  # noqa
except ImportError:
    pass


def cupy_zeros(shape, dtype):
    return cupy.zeros(shape, dtype=dtype)


def cupy_ones(shape, dtype):
    return cupy.ones(shape, dtype=dtype)


def numpy_to_tensor(numpy_array: numpy.ndarray):
    return torch.from_numpy(numpy_array)


def cupy_to_tensor(cupy_array, device: str):
    return torch.as_tensor(cupy_array, device=device)


def cpu_memory_pool():
    return cupy.get_default_pinned_memory_pool()


def gpu_memory_pool():
    return cupy.get_default_memory_pool()


def get_device_count() -> int:
    return cupy.cuda.runtime.getDeviceCount()


def get_device_properties(device_index: int):
    return cupy.cuda.runtime.getDeviceProperties(device_index)


def device_synchronize() -> None:
    return cupy.cuda.runtime.deviceSynchronize()


def ipc_get_mem_handle(device_ptr: int) -> bytes:
    return cupy.cuda.runtime.ipcGetMemHandle(device_ptr)


def ipc_open_mem_handle(handle: bytes, flags: Optional[int] = None) -> int:
    if flags is None:
        flags = cupy.cuda.runtime.cudaIpcMemLazyEnablePeerAccess
    assert isinstance(flags, int)
    return cupy.cuda.runtime.ipcOpenMemHandle(handle, flags)


def ipc_close_mem_handle(device_ptr: int) -> None:
    return cupy.cuda.runtime.ipcCloseMemHandle(device_ptr)


def ipc_get_event_handle(event: int) -> bytes:
    return cupy.cuda.runtime.ipcGetEventHandle(event)


def ipc_open_event_handle(handle: bytes) -> int:
    return cupy.cuda.runtime.ipcOpenEventHandle(handle)


def event_record(event: int, stream: int) -> None:
    return cupy.cuda.runtime.eventRecord(event, stream)


def stream_wait_event(stream: int, event: int, flags=0) -> None:
    # cudaEventWaitDefault == 0
    # cudaEventWaitExternal == 1
    return cupy.cuda.runtime.streamWaitEvent(stream, event, flags)


def stream_synchronize(stream: int) -> None:
    return cupy.cuda.runtime.streamSynchronize(stream)


def memcpy_async(dst: int, src: int, size: int, kind: int, stream: int):
    return cupy.cuda.runtime.memcpyAsync(dst, src, size, kind, stream)


def memcpy_async_host_to_host(dst: int, src: int, size: int, stream: int) -> None:
    assert cupy.cuda.runtime.memcpyHostToHost == 0
    return memcpy_async(dst, src, size, cupy.cuda.runtime.memcpyHostToHost, stream)


def memcpy_async_host_to_device(dst: int, src: int, size: int, stream: int) -> None:
    assert cupy.cuda.runtime.memcpyHostToDevice == 1
    return memcpy_async(dst, src, size, cupy.cuda.runtime.memcpyHostToDevice, stream)


def memcpy_async_device_to_host(dst: int, src: int, size: int, stream: int) -> None:
    assert cupy.cuda.runtime.memcpyDeviceToHost == 2
    return memcpy_async(dst, src, size, cupy.cuda.runtime.memcpyDeviceToHost, stream)


def memcpy_async_device_to_device(dst: int, src: int, size: int, stream: int) -> None:
    assert cupy.cuda.runtime.memcpyDeviceToDevice == 3
    return memcpy_async(dst, src, size, cupy.cuda.runtime.memcpyDeviceToDevice, stream)
