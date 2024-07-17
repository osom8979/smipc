# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from asyncio import get_event_loop, run_coroutine_threadsafe
from typing import Optional

from smipc.decorators.override import override
from smipc.server.base import BaseServer, Channel
from smipc.variables import DEFAULT_ENCODING, INFINITY_QUEUE_SIZE


class AioChannelInterface(ABC):
    @abstractmethod
    async def on_recv(self, data: bytes) -> None:
        raise NotImplementedError


class AioServerInterface(ABC):
    @abstractmethod
    async def on_recv(self, channel: "AioChannel", data: bytes) -> None:
        raise NotImplementedError


class AioChannel(Channel, AioChannelInterface):
    def __init__(
        self,
        key: str,
        prefix: str,
        encoding: str,
        max_queue: int,
        s2c_suffix: str,
        c2s_suffix: str,
        mode: int,
        *,
        server: Optional[AioServerInterface] = None,
    ):
        super().__init__(
            key,
            prefix,
            encoding,
            max_queue,
            s2c_suffix,
            c2s_suffix,
            mode,
            make_fifo=True,
        )
        loop = get_event_loop()
        loop.add_reader(self.reader, self._reader_callback, server)

    def _reader_callback(self, server: Optional[AioServerInterface] = None) -> None:
        header, data = self.recv_with_header()
        if data is None:
            return

        if server is not None:
            coro = server.on_recv(self, data)
        else:
            coro = self.on_recv(data)

        loop = get_event_loop()
        run_coroutine_threadsafe(coro, loop)

    @override
    def close(self) -> None:
        loop = get_event_loop()
        loop.remove_reader(self.reader)
        super().close()

    @override
    async def on_recv(self, data: bytes) -> None:
        pass


class AioServer(BaseServer, AioServerInterface):
    def __getitem__(self, key: str) -> AioChannel:
        return super().__getitem__(key)

    @override
    async def on_recv(self, channel: Channel, data: bytes) -> None:
        pass

    @override
    def open(
        self,
        key: str,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
    ):
        if key in self.keys():
            raise KeyError(f"Already opened channel: '{key}'")
        channel = AioChannel(
            key=key,
            prefix=self.get_prefix(key),
            encoding=encoding,
            max_queue=max_queue,
            s2c_suffix=self._s2c_suffix,
            c2s_suffix=self._c2s_suffix,
            mode=self._mode,
            server=self,
        )
        self.add_channel(channel)
        return channel
