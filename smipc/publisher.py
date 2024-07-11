# -*- coding: utf-8 -*-

import os
from typing import Optional

from smipc.pipe.temp import TemporaryPipe
from smipc.protocol import SmipcProtocol
from smipc.variables import (
    DEFAULT_ENCODING,
    DEFAULT_FILE_MODE,
    INFINITY_QUEUE_SIZE,
    PUB2SUB_SUFFIX,
    SUB2PUB_SUFFIX,
)


class SmipcPublisher:
    def __init__(
        self,
        prefix: str,
        max_queue=INFINITY_QUEUE_SIZE,
        open_timeout: Optional[float] = None,
        encoding=DEFAULT_ENCODING,
        mode=DEFAULT_FILE_MODE,
        p2s_suffix=PUB2SUB_SUFFIX,
        s2p_suffix=SUB2PUB_SUFFIX,
    ):
        p2s_path = prefix + p2s_suffix
        s2p_path = prefix + s2p_suffix

        if os.path.exists(p2s_path):
            raise FileExistsError(f"p2s file already exists: '{p2s_path}'")
        if os.path.exists(s2p_path):
            raise FileExistsError(f"s2p file already exists: '{s2p_path}'")

        self._p2s = TemporaryPipe(p2s_path, mode=mode)
        self._s2p = TemporaryPipe(s2p_path, mode=mode)
        assert self._p2s.path == p2s_path
        assert self._s2p.path == s2p_path
        assert os.path.exists(p2s_path)
        assert os.path.exists(s2p_path)

        self._proto = SmipcProtocol(
            reader_path=s2p_path,
            writer_path=p2s_path,
            max_queue=max_queue,
            open_timeout=open_timeout,
            encoding=encoding,
        )

    def close(self):
        self._proto.close()

    def cleanup(self):
        self._p2s.cleanup()
        self._s2p.cleanup()

    def recv(self):
        return self._proto.recv()

    def send(self, data: bytes):
        return self._proto.send(data)
