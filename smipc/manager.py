# -*- coding: utf-8 -*-

from os import PathLike
from typing import Dict, Union

from smipc.memory.queue import SharedMemoryQueue
from smipc.pipe.duplex import FullDuplexPipe
from smipc.pipe.temp import TemporaryPipe


class _PipeConnector:
    file: TemporaryPipe
    pipe: FullDuplexPipe


class SmipcManager:
    _pipes: Dict[str, FullDuplexPipe]
    _files: Dict[str, TemporaryPipe]

    def __init__(
        self,
        root_dir: Union[str, bytes, PathLike[str], PathLike[bytes]],
        mode=0o666,
    ):
        self._root_dir = root_dir
        self._mode = mode
        self._pipes = dict()
        self._files = dict()

    def open(self, key: str) -> None:
        self._pipes[key] = FullDuplexPipe()

    def close(self, key: str) -> bytes:
        pass

    def recv(self, key: str) -> bytes:
        pass

    def send(self, key: str, data: bytes) -> None:
        pass
