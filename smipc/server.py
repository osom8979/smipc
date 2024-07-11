# -*- coding: utf-8 -*-

import os
from typing import Dict, Optional

from smipc.publisher import SmipcPublisher
from smipc.variables import (
    DEFAULT_ENCODING,
    DEFAULT_FILE_MODE,
    INFINITY_QUEUE_SIZE,
    PUB2SUB_SUFFIX,
    SUB2PUB_SUFFIX,
)


class SmipcServer:
    _pubs: Dict[str, SmipcPublisher]

    def __init__(
        self,
        root: str,
        max_queue=INFINITY_QUEUE_SIZE,
        open_timeout: Optional[float] = None,
        encoding=DEFAULT_ENCODING,
        mode=DEFAULT_FILE_MODE,
        p2s_suffix=PUB2SUB_SUFFIX,
        s2p_suffix=SUB2PUB_SUFFIX,
    ):
        self._root = root
        self._max_queue = max_queue
        self._open_timeout = open_timeout
        self._encoding = encoding
        self._mode = mode
        self._p2s_suffix = p2s_suffix
        self._s2p_suffix = s2p_suffix
        self._pubs = dict()

    def get_prefix(self, key: str) -> str:
        return os.path.join(self._root, key)

    def open(self, key: str) -> None:
        if key in self._pubs:
            raise KeyError(f"Already opened publisher: '{key}'")

        self._pubs[key] = SmipcPublisher(
            prefix=self.get_prefix(key),
            max_queue=self._max_queue,
            open_timeout=self._open_timeout,
            encoding=self._encoding,
            mode=self._mode,
            s2p_suffix=self._s2p_suffix,
            p2s_suffix=self._p2s_suffix,
        )

    def close(self, key: str):
        self._pubs[key].close()

    def recv(self, key: str):
        return self._pubs[key].recv()

    def send(self, key: str, data: bytes):
        return self._pubs[key].send(data)
