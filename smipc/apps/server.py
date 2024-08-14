# -*- coding: utf-8 -*-

import os
from asyncio import sleep
from typing import Callable, Optional

from smipc.aio.run import aio_run
from smipc.arguments import DEFAULT_CHANNEL, LOCAL_ROOT_DIR
from smipc.decorators.override import override
from smipc.server.aio.base import AioChannel
from smipc.server.aio.echo import AioEchoServer


class _AioEchoServer(AioEchoServer):
    def __init__(
        self,
        root: str,
        use_cuda: bool,
        printer: Callable[..., None],
    ):
        super().__init__(root)
        self._use_cuda = use_cuda
        self._printer = printer

    @override
    async def on_recv(self, channel: AioChannel, data: bytes) -> None:
        self._printer(f"recv: {len(data)}bytes")
        await super().on_recv(channel, data)


async def run_echo_server(
    root_dir: str,
    channel: str,
    use_cuda: bool,
    printer: Callable[..., None],
) -> None:
    server = _AioEchoServer(root_dir, use_cuda, printer)
    server.open(channel)

    while True:
        await sleep(1.0)


def run_server(
    root_dir: Optional[str] = None,
    channel=DEFAULT_CHANNEL,
    use_cuda=False,
    use_uvloop=False,
    printer: Callable[..., None] = print,
) -> None:
    if not root_dir:
        root_dir = os.path.join(os.getcwd(), LOCAL_ROOT_DIR)

    assert root_dir is not None
    assert isinstance(root_dir, str)
    assert len(channel) >= 1

    aio_run(run_echo_server(root_dir, channel, use_cuda, printer), use_uvloop)
