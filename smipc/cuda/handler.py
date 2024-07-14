# -*- coding: utf-8 -*-

from typing import Optional

from smipc.cuda.memory import CudaMemory


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
