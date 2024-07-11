# -*- coding: utf-8 -*-

import os
from typing import Optional

from smipc.protocol import SmipcProtocol
from smipc.variables import (
    DEFAULT_ENCODING,
    INFINITY_QUEUE_SIZE,
    PUB2SUB_SUFFIX,
    SUB2PUB_SUFFIX,
)


class SmipcSubscriber:
    def __init__(
        self,
        prefix: str,
        max_queue=INFINITY_QUEUE_SIZE,
        open_timeout: Optional[float] = None,
        encoding=DEFAULT_ENCODING,
        p2s_suffix=PUB2SUB_SUFFIX,
        s2p_suffix=SUB2PUB_SUFFIX,
    ):
        p2s_path = prefix + p2s_suffix
        s2p_path = prefix + s2p_suffix

        if not os.path.exists(p2s_path):
            raise FileNotFoundError(f"p2s file does not exist: '{p2s_path}'")
        if not os.path.exists(s2p_path):
            raise FileNotFoundError(f"s2p file does not exist: '{s2p_path}'")

        self._proto = SmipcProtocol(
            reader_path=p2s_path,
            writer_path=s2p_path,
            max_queue=max_queue,
            open_timeout=open_timeout,
            encoding=encoding,
        )

    def close(self):
        self._proto.close()

    def recv(self):
        return self._proto.recv()

    def send(self, data: bytes):
        return self._proto.send(data)
