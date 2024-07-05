# -*- coding: utf-8 -*-

from os import PathLike, mkfifo
from typing import Union

from smipc.memory.queue import SharedMemoryQueue


class SmipcServer:
    def __init__(
        self,
        root: Union[str, bytes, PathLike[str], PathLike[bytes]],
        size=1,
        mode=0o666,
    ):
        self._root = root
        self._size = size
        self._mode = mode

    def start(self):
        pass

    def stop(self):
        pass

    def recv(self, index: int) -> bytes:
        assert 0 <= index < self._size

    def send(self, index: int, data: bytes) -> None:
        assert 0 <= index < self._size
