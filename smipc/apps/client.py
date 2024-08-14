# -*- coding: utf-8 -*-

import os
from dataclasses import dataclass
from typing import Callable, Optional

from smipc.aio.run import aio_run
from smipc.arguments import (
    DEFAULT_CHANNEL,
    DEFAULT_DATA_SIZE,
    DEFAULT_ITERATION,
    LOCAL_ROOT_DIR,
)
from smipc.server.aio.queue import AioQueueChannel


@dataclass
class _Result:
    client: Optional[AioQueueChannel] = None


async def create_client(
    root_dir: str,
    channel: str,
    use_cuda: bool,
    printer: Callable[..., None],
    result: _Result,
) -> None:
    pass


def run_client(
    root_dir: Optional[str] = None,
    channel=DEFAULT_CHANNEL,
    iteration=DEFAULT_ITERATION,
    data_size=DEFAULT_DATA_SIZE,
    use_cuda=False,
    use_uvloop=False,
    printer: Callable[..., None] = print,
) -> None:
    if not root_dir:
        root_dir = os.path.join(os.getcwd(), LOCAL_ROOT_DIR)

    assert root_dir is not None
    assert isinstance(root_dir, str)
    assert len(channel) >= 1
    assert iteration >= 1
    assert data_size >= 1

    result = _Result()
    aio_run(create_client(root_dir, channel, use_cuda, printer, result), use_uvloop)
