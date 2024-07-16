# -*- coding: utf-8 -*-

from os import PathLike
from threading import Event
from typing import Optional, Union

from smipc.decorators.override import override
from smipc.pipe.duplex import FullDuplexPipe
from smipc.protocols.base import BaseProtocol
from smipc.sm.queue import SharedMemoryQueue
from smipc.sm.written import SmWritten
from smipc.variables import DEFAULT_ENCODING, INFINITY_QUEUE_SIZE


class SmProtocol(BaseProtocol):
    def __init__(
        self,
        pipe: FullDuplexPipe,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
    ):
        super().__init__(
            pipe=pipe,
            encoding=encoding,
            force_sm_over_pipe=False,
            disable_restore_sm=False,
        )
        self._sms = SharedMemoryQueue(max_queue)

    @classmethod
    def from_fifo(
        cls,
        reader_path: Union[str, PathLike[str]],
        writer_path: Union[str, PathLike[str]],
        open_timeout: Optional[float] = None,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
        *,
        interval=0.001,
        blocking: Optional[Event] = None,
    ):
        pipe = FullDuplexPipe.from_fifo(
            writer_path,
            reader_path,
            open_timeout,
            interval=interval,
            blocking=blocking,
        )
        return cls(pipe=pipe, encoding=encoding, max_queue=max_queue)

    @override
    def close_sm(self) -> None:
        self._sms.clear()

    @override
    def write_sm(self, data: bytes) -> SmWritten:
        return self._sms.write(data)

    @override
    def read_sm(self, name: bytes, size: int) -> bytes:
        sm_name = str(name, encoding=self._encoding)
        return SharedMemoryQueue.read(sm_name, size=size)

    @override
    def restore_sm(self, name: bytes) -> None:
        self._sms.restore(str(name, encoding=self._encoding))
