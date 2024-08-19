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
    debug=False,
    verbose=0,
    printer: Callable[..., None] = print,
) -> None:
    if not root:
        root = os.path.join(os.getcwd(), LOCAL_ROOT_DIR)

    assert root is not None
    assert isinstance(root, str)
    assert len(key) >= 1
    assert iteration >= 1
    assert data_size >= 1

    def _log_message(message: str, index: Optional[int] = None) -> str:
        if index is not None:
            if verbose >= 1:
                return f"{datetime.now()} Channel[{key}] #{index:04} {message}"
            else:
                return f"Channel[{key}] #{index:04} {message}"
        else:
            if verbose >= 1:
                return f"{datetime.now()} Channel[{key}] {message}"
            else:
                return f"Channel[{key}] {message}"

    def log_info(message: str, index: Optional[int] = None) -> None:
        printer(_log_message(message, index))

    def log_debug(message: str, index: Optional[int] = None) -> None:
        if debug:
            printer(_log_message(message, index))

    request = b"\x00" * data_size
    total_duration = 0.0
    drop_first = True
    blocking = True

    log_info(f"open(blocking={blocking}) ...")
    client = BaseClient.from_root(root, key, blocking=blocking)
    log_info("open() -> OK")

    try:
        for i in range(iteration):
            if i % 100 == 0:
                log_info(f"Iteration #{i}")

            log_debug(f"send({len(request)}bytes) ...", index=i)

            send_begin = time()
            written = client.send(request)
            send_end = time()

            send_duration = send_end - send_begin
            log_debug(f"send() -> {written} (duration: {send_duration:.3f}s)", index=i)

            log_debug("recv() ...", index=i)
            recv_begin = time()
            while True:
                try:
                    response = client.recv()
                    if response is not None:
                        break
                    log_debug("recv() -> None", index=i)
                except BaseException as e:
                    log_debug(f"{type(e)}: {str(e)}", index=i)
            recv_end = time()

            recv_duration = recv_end - recv_begin
            log_debug(
                f"recv() -> {len(request)}bytes (duration: {recv_duration:.3f}s)",
                index=i,
            )

            duration = recv_end - send_begin

            if not (drop_first and i == 0):
                total_duration += duration

            assert response is not None
            if request != response:
                raise ValueError("Request data and response data are different")
    except BaseException as e:
        log_info(f"{type(e)}: {str(e)}")
    else:
        mean_duration = total_duration / (iteration - (1 if drop_first else 0))
        log_info(f"Mean duration: {mean_duration:.3f}s (iteration={iteration})")
    finally:
        client.close()
