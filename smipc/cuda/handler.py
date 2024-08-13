# -*- coding: utf-8 -*-

from functools import reduce
from typing import Optional, Sequence

import numpy

from smipc.cuda.alignment import IPC_ALLOCATION_UNIT_SIZE, align_ipc_malloc_size
from smipc.cuda.memory import CudaMemory

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


def cpu_memory_pool():
    return cupy.get_default_pinned_memory_pool()


def gpu_memory_pool():
    return cupy.get_default_memory_pool()


def get_device_count():
    return cupy.cuda.runtime.getDeviceCount()


def get_device_properties(device_index: int):
    return cupy.cuda.runtime.getDeviceProperties(device_index)


def ipc_get_mem_handle(device_ptr: int) -> bytes:
    return cupy.cuda.runtime.ipcGetMemHandle(device_ptr)


def ipc_open_mem_handle(handle: bytes, flags: Optional[int] = None) -> int:
    if flags is None:
        flags = cupy.cuda.runtime.cudaIpcMemLazyEnablePeerAccess
    assert isinstance(flags, int)
    return cupy.cuda.runtime.ipcOpenMemHandle(handle, flags)


def ipc_close_mem_handle(device_ptr: int):
    return cupy.cuda.runtime.ipcCloseMemHandle(device_ptr)


def ipc_get_event_handle(event: int) -> bytes:
    return cupy.cuda.runtime.ipcGetEventHandle(event)


def ipc_open_event_handle(handle: bytes) -> int:
    return cupy.cuda.runtime.ipcOpenEventHandle(handle)


def stream_wait_event(stream: int, event: int, flags=0):
    # cudaEventWaitDefault == 0
    # cudaEventWaitExternal == 1
    return cupy.cuda.runtime.streamWaitEvent(stream, event, flags)


def memcpy_async(dst: int, src: int, size: int, kind: int, stream: int):
    return cupy.cuda.runtime.memcpyAsync(dst, src, size, kind, stream)


def memcpy_async_host_to_device(dst: int, src: int, size: int, stream: int):
    assert cupy.cuda.runtime.memcpyHostToDevice == 1
    return memcpy_async(dst, src, size, cupy.cuda.runtime.memcpyHostToDevice, stream)


def memcpy_async_device_to_host(dst: int, src: int, size: int, stream: int):
    assert cupy.cuda.runtime.memcpyDeviceToHost == 2
    return memcpy_async(dst, src, size, cupy.cuda.runtime.memcpyDeviceToHost, stream)


class IpcReceiver:
    def __init__(self, mem: CudaMemory):
        self._shape = mem.shape
        self._memory_size = mem.memory_size
        self._stride = mem.stride

        self._device_ptr = ipc_open_mem_handle(mem.memory_handle)
        self._um = cupy.cuda.UnownedMemory(self._device_ptr, mem.memory_size, 0)
        self._mp = cupy.cuda.MemoryPointer(self._um, 0)

        self._device = cupy.cuda.Device(device=mem.device_index)
        self._event_ptr = ipc_open_event_handle(mem.event_handle)
        self._stream = cupy.cuda.get_current_stream(mem.device_index)

    def close(self):
        ipc_close_mem_handle(self._device_ptr)

    def record(self):
        cupy.cuda.runtime.eventRecord(self._event_ptr, self._stream.ptr)

    def wait(self):
        stream_wait_event(self._stream.ptr, self._event_ptr)

    def as_gpu(self, dtype):
        return cupy.ndarray(self._shape, dtype=dtype, memptr=self._mp)


class CudaHandler:
    def __init__(self, shape: Sequence[int], dtype, stride=0, device=None):
        size = reduce(lambda x, y: x * y, shape, 1)

        if size <= 0:
            raise ValueError("size must be positive")

        self._size = align_ipc_malloc_size(size)
        self._stride = stride

        assert self._size >= IPC_ALLOCATION_UNIT_SIZE
        assert self._size % IPC_ALLOCATION_UNIT_SIZE == 0

        self._device = cupy.cuda.Device(device=device)
        self._stream = cupy.cuda.Stream(non_blocking=True)
        self._event = cupy.cuda.Event(
            block=False,
            disable_timing=True,
            interprocess=True,
        )

        with self._device:
            self._cpu_memory = cpu_memory_pool().malloc(self._size)
            self._gpu_memory = gpu_memory_pool().malloc(self._size)

        self._cpu = numpy.ndarray(shape=shape, dtype=dtype, buffer=self._cpu_memory)  # type: ignore[var-annotated] # noqa E501
        self._gpu = cupy.ndarray(shape=shape, dtype=dtype, memptr=self._gpu_memory)

        self._event_handle = ipc_get_event_handle(self._event.ptr)
        self._memory_handle = ipc_get_mem_handle(self._gpu.data.ptr)

        self._mem = CudaMemory(
            self._device.id,
            self._event_handle,
            self._memory_handle,
            self._size,
            self._stride,
            self._cpu.shape,
        )

    @property
    def device(self):
        return self._device

    @property
    def device_id(self):
        return self._device.id

    @property
    def device_name(self):
        return f"cuda:{self._device.id}"

    @property
    def cpu(self):
        return self._cpu

    @property
    def gpu(self):
        return self._gpu

    @property
    def event(self):
        return self._event

    @property
    def stream(self):
        return self._stream

    @property
    def mem(self):
        return self._mem

    @property
    def size(self):
        return self._size

    @property
    def stride(self):
        return self._stride

    def as_cpu_tensor(self):
        return torch.from_numpy(self._cpu)

    def as_gpu_tensor(self):
        return torch.as_tensor(self._gpu, device=self.device_name)

    def async_copy_host_to_device(self) -> None:
        memcpy_async_host_to_device(
            self._gpu_memory.ptr,
            self._cpu_memory.ptr,
            self._size,
            self._stream.ptr,
        )

    def async_copy_device_to_host(self) -> None:
        memcpy_async_device_to_host(
            self._cpu_memory.ptr,
            self._gpu_memory.ptr,
            self._size,
            self._stream.ptr,
        )

    def record(self) -> None:
        self._event.record(self._stream)

    def synchronize(self) -> None:
        self._stream.synchronize()
