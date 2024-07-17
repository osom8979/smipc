# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from asyncio import get_event_loop, run_coroutine_threadsafe

from smipc.decorators.override import override
from smipc.server.base import BaseServer, Channel
from smipc.variables import (
    DEFAULT_ENCODING,
    DEFAULT_FILE_MODE,
    INFINITY_QUEUE_SIZE,
    PUB2SUB_SUFFIX,
    SUB2PUB_SUFFIX,
)


class AioServerInterface(ABC):
    @abstractmethod
    async def on_recv(self, channel: Channel, data: bytes) -> None:
        raise NotImplementedError


class AioServer(AioServerInterface):
    def __init__(
        self,
        root: str,
        mode=DEFAULT_FILE_MODE,
        *,
        s2c_suffix=PUB2SUB_SUFFIX,
        c2s_suffix=SUB2PUB_SUFFIX,
        make_root=True,
    ):
        self._server = BaseServer(
            root=root,
            mode=mode,
            s2c_suffix=s2c_suffix,
            c2s_suffix=c2s_suffix,
            make_root=make_root,
        )

    @property
    def root(self):
        return self._server.root

    def __getitem__(self, key: str):
        return self._server.__getitem__(key)

    def __len__(self) -> int:
        return self._server.__len__()

    def keys(self):
        return self._server.keys()

    def values(self):
        return self._server.values()

    def get_prefix(self, key: str) -> str:
        return self._server.get_prefix(key)

    @override
    async def on_recv(self, channel: Channel, data: bytes) -> None:
        pass

    def _reader_callback(self, channel: Channel) -> None:
        header, data = channel.recv_with_header()
        if data is None:
            return

        loop = get_event_loop()
        coro = self.on_recv(channel, data)
        run_coroutine_threadsafe(coro, loop)

    def open(
        self,
        key: str,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
    ):
        channel = self._server.open(key, encoding=encoding, max_queue=max_queue)
        loop = get_event_loop()
        loop.add_reader(channel.reader, self._reader_callback, channel)
        return channel

    def close(self, key: str) -> None:
        channel = self._server[key]
        loop = get_event_loop()
        loop.remove_reader(channel.reader)
        channel.close()

    def cleanup(self, key: str) -> None:
        self._server[key].cleanup()

    def send(self, key: str, data: bytes):
        return self._server[key].send(data)
