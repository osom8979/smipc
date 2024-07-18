# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from asyncio import get_event_loop, run_coroutine_threadsafe
from typing import Optional
from weakref import ReferenceType

from smipc.decorators.override import override
from smipc.pipe.temp_pair import TemporaryPipePair
from smipc.protocols.sm import SmProtocol
from smipc.server.base import BaseServer, Channel


def _aio_channel_reader(channel: "AioChannel") -> None:
    header, data = channel.proto.recv_with_header()
    if data is None:
        return

    base = channel.base
    if base is not None:
        assert isinstance(base, AioServer)
        coro = base.on_recv(channel, data)
    else:
        coro = channel.on_recv(data)

    loop = get_event_loop()
    run_coroutine_threadsafe(coro, loop)


class AioChannelInterface(ABC):
    @abstractmethod
    async def on_recv(self, data: bytes) -> None:
        raise NotImplementedError


class AioChannel(Channel, AioChannelInterface):
    def __init__(
        self,
        key: str,
        proto: SmProtocol,
        weak_base: Optional[ReferenceType["BaseServer"]] = None,
        fifos: Optional[TemporaryPipePair] = None,
    ):
        super().__init__(key, proto, weak_base, fifos)
        loop = get_event_loop()
        loop.add_reader(self.reader, _aio_channel_reader, self)

    @override
    def close(self) -> None:
        loop = get_event_loop()
        loop.remove_reader(self.reader)
        super().close()

    @override
    def recv_with_header(self):
        raise RuntimeError(
            f"{type(self).__name__} requires data to be received through callbacks"
        )

    @override
    def recv(self):
        raise RuntimeError(
            f"{type(self).__name__} requires data to be received through callbacks"
        )

    @override
    async def on_recv(self, data: bytes) -> None:
        pass


class AioServerInterface(ABC):
    @abstractmethod
    async def on_recv(self, channel: AioChannel, data: bytes) -> None:
        raise NotImplementedError


class AioServer(BaseServer, AioServerInterface):
    @override
    def on_create_channel(
        self,
        key: str,
        proto: SmProtocol,
        weak_base: Optional[ReferenceType],
        fifos: Optional[TemporaryPipePair],
    ):
        return AioChannel(key, proto, weak_base, fifos)

    @override
    async def on_recv(self, channel: AioChannel, data: bytes) -> None:
        pass

    def create_synced_client_channel(self, key: str, blocking=False):
        paths = self.get_path_pair(key, flip=True)
        pipe = self.create_pipe(paths, blocking=blocking, no_faker=True)
        proto = self.create_proto(pipe)
        return BaseServer.on_create_channel(self, key, proto, None, None)
