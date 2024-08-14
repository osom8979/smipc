# -*- coding: utf-8 -*-

from typing import Optional

import numpy

from smipc.cuda.ipc.packet import CudaIpcPacket
from smipc.cuda.runtime import (
    cpu_memory_pool,
    cupy_to_tensor,
    event_record,
    ipc_close_mem_handle,
    ipc_open_event_handle,
    ipc_open_mem_handle,
    memcpy_async_device_to_host,
    memcpy_async_host_to_device,
    numpy_to_tensor,
    stream_wait_event,
)

try:
    import cupy  # noqa
except ImportError:
    pass


class CudaIpcReceiver:
    _cpu: Optional[numpy.ndarray]

    def __init__(self, info: CudaIpcPacket, lazy_cpu=True):
        self._info = info
        self._device = cupy.cuda.Device(device=info.device_index)

        with self._device:
            self._stream = cupy.cuda.get_current_stream(info.device_index)
            self._event_ptr = ipc_open_event_handle(info.event_handle)
            self._device_ptr = ipc_open_mem_handle(info.memory_handle)

            self._cpu_memory = None
            self._cpu = None

            if not lazy_cpu:
                self.init_cpu()

            um = cupy.cuda.UnownedMemory(
                ptr=self._device_ptr,
                size=info.memory_size,
                owner=0,
                device_id=self._device.id,
            )
            mp = cupy.cuda.MemoryPointer(mem=um, offset=0)

            self._gpu = cupy.ndarray(info.shape, dtype=info.dtype, memptr=mp)

    def init_cpu(self):
        if self._cpu is not None:
            raise ValueError("CPU memory already initialized")

        with self._device:
            self._cpu_memory = cpu_memory_pool().malloc(self._info.memory_size)

        self._cpu = numpy.ndarray(
            shape=self._info.shape,
            dtype=self._info.dtype,
            buffer=self._cpu_memory,
        )

    def close(self):
        ipc_close_mem_handle(self._device_ptr)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

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
        if self._cpu is None:
            self.init_cpu()
        assert self._cpu is not None
        return self._cpu

    @property
    def gpu(self):
        return self._gpu

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
        if self._cpu is None:
            self.init_cpu()
        assert self._cpu is not None
        return numpy_to_tensor(self._cpu)

    def as_gpu_tensor(self):
        return cupy_to_tensor(self._gpu, device=self.device_name)

    def async_copy_host_to_device(self) -> None:
        if self._cpu_memory is None:
            self.init_cpu()

        assert self._cpu_memory is not None
        memcpy_async_host_to_device(
            self._device_ptr,
            self._cpu_memory.ptr,
            self._info.memory_size,
            self._stream.ptr,
        )

    def async_copy_device_to_host(self) -> None:
        if self._cpu_memory is None:
            self.init_cpu()

        assert self._cpu_memory is not None
        memcpy_async_device_to_host(
            self._cpu_memory.ptr,
            self._device_ptr,
            self._info.memory_size,
            self._stream.ptr,
        )

    def record(self):
        event_record(self._event_ptr, self._stream.ptr)

    def wait_event(self):
        stream_wait_event(self._stream.ptr, self._event_ptr)

    def synchronize(self) -> None:
        self._stream.synchronize()
