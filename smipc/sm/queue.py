# -*- coding: utf-8 -*-

from collections import deque
from multiprocessing.shared_memory import SharedMemory
from queue import Full
from typing import Deque, Dict, Optional, Union
from weakref import finalize

from smipc.sm.utils import create_shared_memory, destroy_shared_memory
from smipc.sm.written import SmWritten
from smipc.variables import INFINITY_QUEUE_SIZE


class SharedMemoryQueue:
    _waiting: Deque[SharedMemory]
    _working: Dict[str, SharedMemory]

    def __init__(self, max_queue=INFINITY_QUEUE_SIZE):
        self._max_queue = max_queue
        self._waiting = deque()
        self._working = dict()
        self._finalizer = finalize(self, self._cleanup, self._waiting, self._working)

    @staticmethod
    def _cleanup(waiting: Deque[SharedMemory], working: Dict[str, SharedMemory]):
        while waiting:
            sm = waiting.popleft()
            destroy_shared_memory(sm)
        while working:
            _, sm = working.popitem()
            destroy_shared_memory(sm)
        assert not waiting
        assert not working

    def cleanup(self) -> None:
        if self._finalizer.detach():
            self._cleanup(self._waiting, self._working)
            del self._waiting
            del self._working

    def clear_waiting(self):
        while self._waiting:
            sm = self._waiting.popleft()
            destroy_shared_memory(sm)
        assert not self._waiting

    def clear_working(self):
        while self._working:
            _, sm = self._working.popitem()
            destroy_shared_memory(sm)
        assert not self._working

    def clear(self):
        self.clear_waiting()
        self.clear_working()

    @property
    def max_queue(self) -> int:
        return self._max_queue

    @property
    def has_queue_limitation(self) -> bool:
        return self._max_queue > 0

    @property
    def is_infinity(self) -> bool:
        return not self.has_queue_limitation

    @property
    def size_waiting(self) -> int:
        return len(self._waiting)

    @property
    def size_working(self) -> int:
        return len(self._working)

    @property
    def size(self) -> int:
        return self.size_waiting + self.size_working

    @property
    def is_full(self) -> bool:
        if self.is_infinity:
            return False
        if self.size_waiting >= 1:
            return False
        return self.size_waiting >= self._max_queue

    def find_working(self, key: str) -> SharedMemory:
        return self._working[key]

    def _add_worker_safe(self, buffer_size: int) -> SharedMemory:
        if self.is_full:
            raise Full

        if len(self._waiting) >= 1:
            sm = self._waiting.popleft()
            if sm.size < buffer_size:
                destroy_shared_memory(sm)
                sm = create_shared_memory(buffer_size)
        else:
            sm = create_shared_memory(buffer_size)

        assert sm is not None
        assert sm.size >= buffer_size
        self._working[sm.name] = sm
        return sm

    def write_bytes(self, data: bytes, offset=0) -> SmWritten:
        end = offset + len(data)
        sm = self._add_worker_safe(end)
        sm.buf[offset:end] = data
        return SmWritten(sm.name, offset, end)

    def write(self, data: Union[bytes, memoryview], offset=0) -> SmWritten:
        if isinstance(data, memoryview):
            return self.write(data.tobytes(), offset)
        else:
            assert isinstance(data, bytes)
            return self.write_bytes(data, offset)

    def restore(self, name: str) -> None:
        self._waiting.append(self._working.pop(name))

    @staticmethod
    def read(name: str, offset=0, size: Optional[int] = None) -> bytes:
        sm = SharedMemory(name=name)
        try:
            if size is None:
                return bytes(sm.buf[offset:])
            else:
                if size <= 0:
                    raise ValueError("The 'size' argument must be greater than 0")
                end = offset + size
                return bytes(sm.buf[offset:end])
        finally:
            sm.close()

    class RentalManager:
        __slots__ = ("_sm", "_smq")

        def __init__(self, sm: SharedMemory, smq: "SharedMemoryQueue"):
            self._sm = sm
            self._smq = smq

        def __enter__(self) -> SharedMemory:
            return self._sm

        def __exit__(self, exc_type, exc_value, tb):
            self._smq.restore(self._sm.name)

    def rent(self, buffer_byte: int) -> RentalManager:
        return self.RentalManager(self._add_worker_safe(buffer_byte), self)

    class MultiRentalManager:
        __slots__ = ("_sms", "_smq")

        def __init__(self, sms: Dict[str, SharedMemory], smq: "SharedMemoryQueue"):
            self._sms = sms
            self._smq = smq

        def __enter__(self) -> Dict[str, SharedMemory]:
            return self._sms

        def __exit__(self, exc_type, exc_value, tb):
            for sm in self._sms.values():
                self._smq.restore(sm.name)

    def multi_rent(self, rental_size: int, buffer_byte: int) -> MultiRentalManager:
        if rental_size <= 0 or buffer_byte <= 0:
            return self.MultiRentalManager(dict(), self)

        sms = Dict[str, SharedMemory]()
        for _ in range(rental_size):
            try:
                sm = self._add_worker_safe(buffer_byte)
            except Full:
                for sm_name in sms.keys():
                    self.restore(sm_name)
                raise
            else:
                sms[sm.name] = sm

        return self.MultiRentalManager(sms=sms, smq=self)
