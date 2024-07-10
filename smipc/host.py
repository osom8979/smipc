# -*- coding: utf-8 -*-

from os import PathLike
from typing import Union

from smipc.memory.queue import SharedMemoryQueue


class SmipcHost:
    def __init__(
        self,
        root: Union[str, bytes, PathLike[str], PathLike[bytes]],
        mode=0o666,
    ):
        self._root = root
        self._mode = mode
        self._sms = SharedMemoryQueue()

    def start(self):
        pass

    def stop(self):
        pass

    def recv(self, name: str) -> bytes:
        pass

    def send(self, index: int, data: bytes) -> None:
        pass
