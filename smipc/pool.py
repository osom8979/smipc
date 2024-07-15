# -*- coding: utf-8 -*-

import os
from typing import Dict, Optional

from smipc.protocols.base import WrittenInfo
from smipc.pubsub.publisher import Publisher
from smipc.variables import (
    DEFAULT_ENCODING,
    DEFAULT_FILE_MODE,
    INFINITY_QUEUE_SIZE,
    PUB2SUB_SUFFIX,
    SUB2PUB_SUFFIX,
)


class SmipcPool:
    _pubs: Dict[str, Publisher]

    def __init__(
        self,
        root: str,
        p2s_suffix=PUB2SUB_SUFFIX,
        s2p_suffix=SUB2PUB_SUFFIX,
    ):
        self._root = root
        self._p2s_suffix = p2s_suffix
        self._s2p_suffix = s2p_suffix
        self._pubs = dict()

    @property
    def root(self):
        return self._root

    def keys(self):
        return self._pubs.keys()

    def values(self):
        return self._pubs.values()

    def get_prefix(self, key: str) -> str:
        return os.path.join(self._root, key)

    def open(
        self,
        key: str,
        open_timeout: Optional[float] = None,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
        mode=DEFAULT_FILE_MODE,
    ) -> None:
        if key in self._pubs:
            raise KeyError(f"Already opened publisher: '{key}'")

        self._pubs[key] = Publisher(
            prefix=self.get_prefix(key),
            open_timeout=open_timeout,
            encoding=encoding,
            max_queue=max_queue,
            p2s_suffix=self._p2s_suffix,
            s2p_suffix=self._s2p_suffix,
            mode=mode,
        )

    def close(self, key: str) -> None:
        self._pubs[key].close()

    def cleanup(self, key: str) -> None:
        self._pubs[key].cleanup()

    def recv(self, key: str) -> Optional[bytes]:
        return self._pubs[key].recv()

    def send(self, key: str, data: bytes) -> WrittenInfo:
        return self._pubs[key].send(data)
