# -*- coding: utf-8 -*-

from io import BufferedWriter
from os import PathLike
from typing import Union


class PipeWriter:
    _file: BufferedWriter

    def __init__(self, path: Union[str, bytes, PathLike[str], PathLike[bytes]]):
        # noinspection PyTypeChecker
        self._file = open(path, mode="wb")
        assert isinstance(self._file, BufferedWriter)
        assert not self._file.readable()
        assert self._file.writable()

    @property
    def file(self):
        return self._file

    @property
    def closed(self):
        return self._file.closed

    def close(self) -> None:
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def write(self, data: bytes) -> int:
        return self._file.write(data)

    def flush(self) -> None:
        self._file.flush()
