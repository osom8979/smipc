# -*- coding: utf-8 -*-

from smipc.decorators.override import override
from smipc.server.aio.base import AioChannel, AioServer


class AioEchoServer(AioServer):
    @override
    async def on_recv(self, channel: AioChannel, data: bytes) -> None:
        channel.send(data)  # Echoes the same data.
