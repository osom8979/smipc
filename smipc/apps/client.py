# -*- coding: utf-8 -*-

import os
from datetime import datetime
from time import time
from typing import Callable, Optional

from smipc.arguments import (
    DEFAULT_CHANNEL,
    DEFAULT_DATA_SIZE,
    DEFAULT_ITERATION,
    LOCAL_ROOT_DIR,
)
from smipc.server.base import BaseClient


def log_prefix(key: str, i: Optional[int] = None) -> str:
    if i is not None:
        return f"{datetime.now()} Channel[{key}] #{i:04}"
    else:
        return f"{datetime.now()} Channel[{key}]"


def run_client(
    root: Optional[str] = None,
    key=DEFAULT_CHANNEL,
    iteration=DEFAULT_ITERATION,
    data_size=DEFAULT_DATA_SIZE,
    use_cuda=False,
    printer: Callable[..., None] = print,
) -> None:
    if not root:
        root = os.path.join(os.getcwd(), LOCAL_ROOT_DIR)

    assert root is not None
    assert isinstance(root, str)
    assert len(key) >= 1
    assert iteration >= 1
    assert data_size >= 1

    request = b"\x00" * data_size
    total_duration = 0.0
    drop_first = True
    blocking = True

    printer(f"{log_prefix(key)} open(blocking={blocking}) ...")
    client = BaseClient.from_root(root, key, blocking=blocking)
    printer(f"{log_prefix(key)} open() -> OK")

    try:
        for i in range(iteration):
            printer(f"{log_prefix(key, i)} send({len(request)}bytes) ...")

            send_begin = time()
            written = client.send(request)
            send_end = time()

            send_duration = send_end - send_begin
            printer(
                f"{log_prefix(key, i)} send() -> {written} "
                f"(duration: {send_duration:.3f}s)"
            )

            printer(f"{log_prefix(key, i)} recv() ...")
            recv_begin = time()
            while True:
                try:
                    response = client.recv()
                    if response is not None:
                        break
                    printer(f"{log_prefix(key, i)} recv() -> None")
                except BaseException as e:
                    printer(f"{log_prefix(key, i)} {type(e)}: {str(e)}")
            recv_end = time()

            recv_duration = recv_end - recv_begin
            printer(
                f"{log_prefix(key, i)} recv() -> {len(request)}bytes "
                f"(duration: {recv_duration:.3f}s)"
            )

            duration = recv_end - send_begin

            if not (drop_first and i == 0):
                total_duration += duration

            assert response is not None
            if request != response:
                raise ValueError("Request data and response data are different")
    except BaseException as e:
        printer(f"{log_prefix(key)} {type(e)}: {str(e)}")
    else:
        mean_duration = total_duration / (iteration - (1 if drop_first else 0))
        printer(f"\nMean duration: {mean_duration:.3f}s (iteration={iteration})")
    finally:
        client.close()
