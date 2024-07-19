# -*- coding: utf-8 -*-

from typing import Optional

from smipc.cuda.memory import CudaMemory

try:
    import cupy
except ImportError:
    pass


def get_device_count():
    return cupy.cuda.runtime.getDeviceCount()


def get_device_properties(device_index: int):
    return cupy.cuda.runtime.getDeviceProperties(device_index)


def ipc_get_mem_handle(device_ptr: int):
    return cupy.cuda.runtime.ipcGetMemHandle(device_ptr)


def ipc_open_mem_handle(handle, flags: Optional[int] = None):
    if flags is None:
        flags = cupy.cuda.runtime.cudaIpcMemLazyEnablePeerAccess
    assert isinstance(flags, int)
    return cupy.cuda.runtime.ipcOpenMemHandle(handle, flags)


def ipc_close_mem_handle(device_ptr: int):
    return cupy.cuda.runtime.ipcCloseMemHandle(device_ptr)


def ipc_get_event_handle(event: int):
    return cupy.cuda.runtime.ipcGetEventHandle(event)


def ipc_open_event_handle(handle):
    return cupy.cuda.runtime.ipcOpenEventHandle(handle)


def alloc_pinned_array(size: int):
    return cupy.cuda.alloc_pinned_memory(size)


class CudaHandler:
    _mem: Optional[CudaMemory]

    def __init__(self, mem: Optional[CudaMemory] = None):
        self._mem = mem

    @property
    def memory(self):
        return self._mem

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
