# -*- coding: utf-8 -*-

import os
from datetime import datetime
from time import sleep
from typing import Callable, Optional

from smipc.arguments import DEFAULT_CHANNEL, LOCAL_ROOT_DIR
from smipc.server.base import BaseServer


def run_server(
    root: Optional[str] = None,
    key=DEFAULT_CHANNEL,
    use_cuda=False,
    printer: Callable[..., None] = print,
) -> None:
    if not root:
        root = os.path.join(os.getcwd(), LOCAL_ROOT_DIR)

    assert root is not None
    assert isinstance(root, str)
    assert len(key) >= 1

    server = BaseServer(root)

    printer(f"{datetime.now()} Channel[{key}] open() ...")
    channel = server.open(key)
    printer(f"{datetime.now()} Channel[{key}] open() -> OK")

    printer(f"{datetime.now()} Channel[{key}] set blocking mode ...")
    assert not channel.proto.pipe.reader.blocking
    assert not channel.proto.pipe.writer.blocking
    channel.proto.pipe.reader.blocking = True
    channel.proto.pipe.writer.blocking = True
    assert channel.proto.pipe.reader.blocking
    assert channel.proto.pipe.writer.blocking
    printer(f"{datetime.now()} Channel[{key}] set blocking mode -> OK")

    try:
        while True:
            printer(f"{datetime.now()} Channel[{key}] recv() ...")
            try:
                request = channel.recv()
            except BaseException as e:
                printer(f"{datetime.now()} {type(e)}: {str(e)}")
                sleep(1.0)
                continue

            if request is None:
                printer(f"{datetime.now()} Channel[{key}] recv() -> None")
                continue

            printer(f"{datetime.now()} Channel[{key}] recv() -> {len(request)}bytes")

            printer(f"{datetime.now()} Channel[{key}] send({len(request)}bytes) ...")
            written = channel.send(request)
            printer(f"{datetime.now()} Channel[{key}] send() -> {written}")
    finally:
        channel.close()
        channel.cleanup()
