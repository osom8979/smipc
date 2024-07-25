# -*- coding: utf-8 -*-

from typing import Optional, Sequence

from smipc.cuda.memory import CudaMemory
from smipc.cuda.utils import IPC_ALLOCATION_UNIT_SIZE, align_ipc_malloc_size

try:
    import numpy  # noqa
except ImportError:
    pass

try:
    import cupy  # noqa
except ImportError:
    pass

try:
    import torch  # noqa
except ImportError:
    pass


def get_device_count():
    return cupy.cuda.runtime.getDeviceCount()


def get_device_properties(device_index: int):
    return cupy.cuda.runtime.getDeviceProperties(device_index)


def ipc_get_mem_handle(device_ptr: int):
    return cupy.cuda.runtime.ipcGetMemHandle(device_ptr)


def ipc_open_mem_handle(handle: bytes, flags: Optional[int] = None):
    if flags is None:
        flags = cupy.cuda.runtime.cudaIpcMemLazyEnablePeerAccess
    assert isinstance(flags, int)
    return cupy.cuda.runtime.ipcOpenMemHandle(handle, flags)


def ipc_close_mem_handle(device_ptr: int):
    return cupy.cuda.runtime.ipcCloseMemHandle(device_ptr)


def ipc_get_event_handle(event: int):
    return cupy.cuda.runtime.ipcGetEventHandle(event)


def ipc_open_event_handle(handle: bytes):
    return cupy.cuda.runtime.ipcOpenEventHandle(handle)


class CudaHandler:
    _mem: Optional[CudaMemory]

    def __init__(self, size: int, device=None):
        if size <= 0:
            raise ValueError("size must be positive")

        self._mem = None
        self._size = align_ipc_malloc_size(size)

        assert self._size >= IPC_ALLOCATION_UNIT_SIZE
        assert self._size % IPC_ALLOCATION_UNIT_SIZE == 0

        self._device = cupy.cuda.Device(device=device)
        self._event = cupy.cuda.Event(
            block=False,
            disable_timing=True,
            interprocess=True,
        )

        with self._device:
            self._cpu = self.cpu_memory_pool().malloc(self._size)
            self._gpu = self.gpu_memory_pool().malloc(self._size)

    @staticmethod
    def cpu_memory_pool():
        return cupy.get_default_pinned_memory_pool()

    @staticmethod
    def gpu_memory_pool():
        return cupy.get_default_memory_pool()

    @property
    def device_id(self):
        return self._device.id

    @property
    def device_name(self):
        return f"cuda:{self._device.id}"

    @property
    def size(self):
        return self._size

    def as_numpy(self, shape: Sequence[int], dtype):
        return numpy.ndarray(shape=shape, dtype=dtype, buffer=self._cpu)

    def as_cupy(self, shape: Sequence[int], dtype):
        return cupy.ndarray(shape=shape, dtype=dtype, memptr=self._gpu)

    def as_cpu_tensor(self, shape: Sequence[int], dtype):
        return torch.from_numpy(self.as_numpy(shape, dtype))

    def as_gpu_tensor(self, shape: Sequence[int], dtype):
        return torch.as_tensor(self.as_cupy(shape, dtype), device=self.device_name)

    def to_async_device(self):
        pass

    def to_async_host(self):
        pass

    def sync(self):
        pass
