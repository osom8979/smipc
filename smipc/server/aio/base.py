# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from asyncio import get_event_loop, run_coroutine_threadsafe
from typing import Optional
from weakref import ReferenceType

from smipc.decorators.override import override
from smipc.pipe.temp_pair import TemporaryPipePair
from smipc.protocols.sm import SmProtocol
from smipc.server.base import (
    BaseServer,
    Channel,
    create_pipe,
    create_proto,
    get_path_pair,
)
from smipc.variables import (
    CLIENT_TO_SERVER_SUFFIX,
    DEFAULT_ENCODING,
    INFINITY_QUEUE_SIZE,
    SERVER_TO_CLIENT_SUFFIX,
)


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


class AioClient(AioChannel):
    def __init__(self, key: str, proto: SmProtocol):
        super().__init__(key, proto)

    @classmethod
    def from_channel(cls, channel: Channel):
        if channel._weak_base is not None:
            raise ValueError("The 'weak_base' attribute of the channel is already set")
        if channel._fifos is not None:
            raise ValueError("The 'fifos' attribute of the channel is already set")

        return cls(channel.key, channel.proto)

    @classmethod
    def from_root(
        cls,
        root: str,
        key: str,
        blocking=False,
        *,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
        s2c_suffix=SERVER_TO_CLIENT_SUFFIX,
        c2s_suffix=CLIENT_TO_SERVER_SUFFIX,
    ):
        paths = get_path_pair(
            root=root,
            key=key,
            flip=True,
            s2c_suffix=s2c_suffix,
            c2s_suffix=c2s_suffix,
        )
        pipe = create_pipe(paths, blocking=blocking, no_faker=True)
        proto = create_proto(pipe, encoding, max_queue)
        return cls(key, proto)


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
