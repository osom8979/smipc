# -*- coding: utf-8 -*-

import os
from datetime import datetime
from time import sleep
from typing import Callable, Optional

from smipc.arguments import DEFAULT_CHANNEL, DEFAULT_ITERATION, LOCAL_ROOT_DIR
from smipc.cuda.ipc.packet import CudaIpcPacket
from smipc.cuda.ipc.receiver import CudaIpcReceiver
from smipc.server.base import BaseServer


def run_server(
    root: Optional[str] = None,
    key=DEFAULT_CHANNEL,
    iteration=DEFAULT_ITERATION,
    use_cuda=False,
    use_cuda_kernel=True,
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

    server = BaseServer(root)

    log_info("open() ...")
    channel = server.open(key)
    log_info("open() -> OK")

    log_info("set blocking mode ...")
    assert not channel.proto.pipe.reader.blocking
    assert not channel.proto.pipe.writer.blocking
    channel.proto.pipe.reader.blocking = True
    channel.proto.pipe.writer.blocking = True
    assert channel.proto.pipe.reader.blocking
    assert channel.proto.pipe.writer.blocking
    log_info("set blocking mode -> OK")

    count = 0
    try:
        while True:  # count < iteration:
            log_debug("recv() ...", index=count)
            try:
                request = channel.recv()
            except BaseException as e:
                if verbose >= 2:
                    log_debug(f"{type(e)}: {str(e)}", index=count)
                sleep(0.1)
                continue

            if request is None:
                log_debug("recv() -> None", index=count)
                continue

            log_debug(f"recv() -> {len(request)}bytes", index=count)

            if use_cuda:
                info = CudaIpcPacket.from_bytes(request)
                receiver = CudaIpcReceiver(info, lazy_cpu=False)

                with receiver:
                    receiver.wait_event()

                    # ------------------------------------
                    # If CPU synchronization is required:
                    # receiver.async_copy_device_to_host()
                    # receiver.synchronize()
                    # ------------------------------------

                    if use_cuda_kernel:
                        with receiver.stream:
                            gpu = receiver.gpu
                            gpu += 1

                        receiver.record()

            log_debug(f"send({len(request)}bytes) ...", index=count)
            written = channel.send(request)
            log_debug(f"send() -> {written}", index=count)
            count += 1
    finally:
        channel.close()
        channel.cleanup()
