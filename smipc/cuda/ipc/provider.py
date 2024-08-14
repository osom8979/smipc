# -*- coding: utf-8 -*-

from functools import reduce
from typing import Sequence

import numpy

from smipc.cuda.alignment import IPC_ALLOCATION_UNIT_SIZE, align_ipc_malloc_size
from smipc.cuda.ipc.packet import CudaIpcPacket
from smipc.cuda.runtime import (
    cpu_memory_pool,
    cupy_to_tensor,
    gpu_memory_pool,
    ipc_get_event_handle,
    ipc_get_mem_handle,
    memcpy_async_device_to_host,
    memcpy_async_host_to_device,
    numpy_to_tensor,
)

try:
    import cupy  # noqa
except ImportError:
    pass


class CudaIpcProvider:
    _cpu: numpy.ndarray

    def __init__(self, shape: Sequence[int], dtype, stride=0, device=None):
        if len(shape) <= 0:
            raise ValueError("'shape' cannot be empty")

        size = reduce(lambda x, y: x * y, shape, 1)
        if size <= 0:
            raise ValueError("size must be positive")

        size = align_ipc_malloc_size(size)
        assert size >= IPC_ALLOCATION_UNIT_SIZE
        assert size % IPC_ALLOCATION_UNIT_SIZE == 0

        self._device = cupy.cuda.Device(device=device)

        with self._device:
            self._stream = cupy.cuda.Stream(non_blocking=True)
            self._event = cupy.cuda.Event(
                block=False,
                disable_timing=True,
                interprocess=True,
            )

            self._cpu_memory = cpu_memory_pool().malloc(size)
            self._gpu_memory = gpu_memory_pool().malloc(size)

            self._cpu = numpy.ndarray(shape=shape, dtype=dtype, buffer=self._cpu_memory)
            self._gpu = cupy.ndarray(shape=shape, dtype=dtype, memptr=self._gpu_memory)

        self._info = CudaIpcPacket(
            device_index=self._device.id,
            event_handle=ipc_get_event_handle(self._event.ptr),
            memory_handle=ipc_get_mem_handle(self._gpu_memory.ptr),
            memory_size=size,
            dtype=dtype,
            stride=stride,
            shape=shape,
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
    def info(self):
        return self._info

    @property
    def size(self):
        return self._info.memory_size

    @property
    def stride(self):
        return self._info.stride

    def as_cpu_tensor(self):
        return numpy_to_tensor(self._cpu)

    def as_gpu_tensor(self):
        return cupy_to_tensor(self._gpu, device=self.device_name)

    def async_copy_host_to_device(self) -> None:
        memcpy_async_host_to_device(
            self._gpu_memory.ptr,
            self._cpu_memory.ptr,
            self._info.memory_size,
            self._stream.ptr,
        )

    def async_copy_device_to_host(self) -> None:
        memcpy_async_device_to_host(
            self._cpu_memory.ptr,
            self._gpu_memory.ptr,
            self._info.memory_size,
            self._stream.ptr,
        )

    def record(self):
        self._event.record(self._stream)

    def wait_event(self):
        self._stream.wait_event(self._event)

    def synchronize(self) -> None:
        self._stream.synchronize()
