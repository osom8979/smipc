# -*- coding: utf-8 -*-

from os import PathLike
from typing import Union


class SmipcServer:
    def __init__(
        self,
        root_dir: Union[str, bytes, PathLike[str], PathLike[bytes]],
        mode=0o666,
    ):
        self._root_dir = root_dir
        self._mode = mode

    def open(self, key: str) -> None:
        pass

    def close(self, key: str) -> bytes:
        pass

    def recv(self, key: str) -> bytes:
        pass

    def send(self, key: str, data: bytes) -> None:
        pass
