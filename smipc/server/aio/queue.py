# -*- coding: utf-8 -*-

from asyncio import Queue
from typing import Optional
from weakref import ReferenceType

from smipc.decorators.override import override
from smipc.pipe.temp_pair import TemporaryPipePair
from smipc.protocols.sm import SmProtocol
from smipc.server.aio.base import AioChannel
from smipc.server.base import BaseServer


class AioQueueChannel(AioChannel):
    _queue: Queue[bytes]

    def __init__(
        self,
        key: str,
        proto: SmProtocol,
        weak_base: Optional[ReferenceType["BaseServer"]] = None,
        fifos: Optional[TemporaryPipePair] = None,
        maxsize=0,
    ):
        super().__init__(
            key=key,
            proto=proto,
            weak_base=weak_base,
            fifos=fifos,
        )
        self._queue = Queue(maxsize)

    @override
    async def on_recv(self, data: bytes) -> None:
        await self._queue.put(data)

    def qsize(self) -> int:
        return self._queue.qsize()

    @property
    def maxsize(self) -> int:
        return self._queue.maxsize

    def empty(self) -> bool:
        return self._queue.empty()

    def full(self) -> bool:
        return self._queue.full()

    async def put(self, item: bytes) -> None:
        return await self._queue.put(item)

    def put_nowait(self, item: bytes) -> None:
        return self._queue.put_nowait(item)

    async def get(self) -> bytes:
        return await self._queue.get()

    def get_nowait(self) -> bytes:
        return self._queue.get_nowait()

    def task_done(self) -> None:
        return self._queue.task_done()

    async def join(self) -> None:
        return await self._queue.join()
