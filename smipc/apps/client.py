# -*- coding: utf-8 -*-

import os
from datetime import datetime
from time import time
from typing import Callable, Optional

import numpy as np

from smipc.arguments import (
    DEFAULT_CHANNEL,
    DEFAULT_FRAME_CHANNELS,
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_WIDTH,
    DEFAULT_ITERATION,
    LOCAL_ROOT_DIR,
)
from smipc.cuda.ipc.provider import CudaIpcProvider
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
    frame_width=DEFAULT_FRAME_WIDTH,
    frame_height=DEFAULT_FRAME_HEIGHT,
    frame_channels=DEFAULT_FRAME_CHANNELS,
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
    assert frame_width >= 1
    assert frame_height >= 1
    assert frame_channels >= 1

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

    array_shape = frame_height, frame_width, frame_channels
    data_size = frame_width * frame_height * frame_channels
    request_data = os.urandom(data_size)
    request_array: np.ndarray
    request_array = np.ndarray(array_shape, dtype=np.uint8, buffer=request_data)
    response_array = np.zeros_like(request_array, dtype=np.uint8)
    total_duration = 0.0
    drop_first = True
    blocking = True

    log_info(f"open(blocking={blocking}) ...")
    client = BaseClient.from_root(root, key, blocking=blocking)
    log_info("open() -> OK")

    provider: Optional[CudaIpcProvider] = None
    provider_packet: Optional[bytes] = None

    if use_cuda:
        provider = CudaIpcProvider(array_shape, dtype=np.uint8)
        provider_packet = provider.info.to_bytes()

    h2d_duration = 0.0
    d2h_duration = 0.0

    try:
        for i in range(iteration):
            if i % 100 == 0:
                log_info(f"Iteration #{i}")

            log_debug(f"send({len(request_data)}bytes) ...", index=i)

            if use_cuda:
                h2d_begin = time()
                assert provider is not None
                provider.cpu[:] = request_array[:]
                provider.async_copy_host_to_device()
                provider.record()
                data = provider_packet
                h2d_end = time()
                h2d_duration = h2d_end - h2d_begin
                log_debug(f"H2D -> (duration: {h2d_duration:.3f}s)", index=i)
            else:
                data = request_data

            send_begin = time()
            written = client.send(data)
            send_end = time()

            send_duration = send_end - send_begin
            log_debug(f"send() -> {written} (duration: {send_duration:.3f}s)", index=i)

            log_debug("recv() ...", index=i)
            recv_begin = time()
            while True:
                try:
                    response_data = client.recv()
                    if response_data is not None:
                        break
                    log_debug("recv() -> None", index=i)
                except BaseException as e:
                    log_debug(f"{type(e)}: {str(e)}", index=i)
            recv_end = time()

            assert response_data is not None
            assert isinstance(response_data, bytes)
            recv_duration = recv_end - recv_begin

            log_debug(
                f"recv() -> {len(response_data)}bytes (duration: {recv_duration:.3f}s)",
                index=i,
            )

            if use_cuda:
                assert provider is not None
                d2h_begin = time()
                provider.wait_event()
                provider.async_copy_device_to_host()
                provider.synchronize()
                response_array[:] = provider.cpu[:]
                d2h_end = time()
                d2h_duration = d2h_end - d2h_begin
                log_debug(f"D2H -> (duration: {d2h_duration:.3f}s)", index=i)

            iter_duration = h2d_duration + send_duration + recv_duration + d2h_duration
            if not (drop_first and i == 0):
                total_duration += iter_duration

            if use_cuda:
                if not np.all((request_array + 1) == response_array):
                    raise ValueError("Request array and response array are different")
            else:
                if request_data != response_data:
                    raise ValueError("Request data and response data are different")
    except BaseException as e:
        log_info(f"{type(e)}: {str(e)}")
    else:
        avg = total_duration / (iteration - (1 if drop_first else 0))
        log_info(f"AVG: {avg:.03f}s (iteration={iteration})")
    finally:
        client.close()
