# -*- coding: utf-8 -*-

from typing import Optional, Sequence

import numpy as np

from smipc.cuda.memory import CudaMemory

try:
    # noinspection PyUnresolvedReferences
    import cupy as cp
except ImportError:
    pass


def get_device_count():
    return cp.cuda.runtime.getDeviceCount()


def get_device_properties(device_index: int):
    return cp.cuda.runtime.getDeviceProperties(device_index)


def ipc_get_mem_handle(device_ptr: int):
    return cp.cuda.runtime.ipcGetMemHandle(device_ptr)


def ipc_open_mem_handle(handle: bytes, flags: Optional[int] = None):
    if flags is None:
        flags = cp.cuda.runtime.cudaIpcMemLazyEnablePeerAccess
    assert isinstance(flags, int)
    return cp.cuda.runtime.ipcOpenMemHandle(handle, flags)


def ipc_close_mem_handle(device_ptr: int):
    return cp.cuda.runtime.ipcCloseMemHandle(device_ptr)


def ipc_get_event_handle(event: int):
    return cp.cuda.runtime.ipcGetEventHandle(event)


def ipc_open_event_handle(handle: bytes):
    return cp.cuda.runtime.ipcOpenEventHandle(handle)


class CudaHandler:
    _mem: Optional[CudaMemory]

    def __init__(self, size: int, device=None):
        if size <= 0:
            raise ValueError("size must be positive")

        self._mem = None
        self._size = size

        self._device = cp.cuda.Device(device=device)
        self._event = cp.cuda.Event(block=False, disable_timing=True, interprocess=True)

        with self._device:
            self._cpu = self.cpu_memory_pool().malloc(size)
            self._gpu = self.gpu_memory_pool().malloc(size)

    @staticmethod
    def cpu_memory_pool():
        return cp.get_default_pinned_memory_pool()

    @staticmethod
    def gpu_memory_pool():
        return cp.get_default_memory_pool()

    def as_numpy(self, shape: Sequence[int], dtype):
        return np.frombuffer(self._cpu, dtype=dtype).reshape(shape)

    def as_cupy(self, shape: Sequence[int], dtype):
        return cp.ndarray(shape, dtype=dtype, memptr=self._gpu)

    def create_ipc(self):
        pass

    def open_ipc(self):
        pass

    def to_device(self):
        pass

    def to_host(self):
        pass

    def sync(self):
        pass

    def as_numpy(self):
        pass

    def as_cupy(self):
        pass

    def as_cpu_tensor(self):
        pass

    def as_cuda_tensor(self):
        pass
