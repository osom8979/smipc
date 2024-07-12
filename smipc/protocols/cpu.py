# -*- coding: utf-8 -*-

from os import PathLike
from typing import Optional, Union

from smipc.decorators.override import override
from smipc.protocols.base import BaseProtocol
from smipc.sm.queue import SharedMemoryQueue, SmWritten
from smipc.variables import DEFAULT_ENCODING, INFINITY_QUEUE_SIZE


class CpuProtocol(BaseProtocol):
    def __init__(
        self,
        reader_path: Union[str, PathLike[str]],
        writer_path: Union[str, PathLike[str]],
        open_timeout: Optional[float] = None,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
    ):
        super().__init__(
            reader_path=reader_path,
            writer_path=writer_path,
            open_timeout=open_timeout,
            encoding=encoding,
        )
        self._sms = SharedMemoryQueue(max_queue)

    @override
    def close_sm(self) -> None:
        self._sms.clear()

    @override
    def read_sm(self, name: bytes, size: int) -> bytes:
        sm_name = str(name, encoding=self._encoding)
        return SharedMemoryQueue.read(sm_name, size=size)

    @override
    def write_sm(self, data: bytes) -> SmWritten:
        return self._sms.write(data)

    @override
    def restore_sm(self, name: bytes) -> None:
        self._sms.restore(str(name, encoding=self._encoding))
