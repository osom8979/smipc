# -*- coding: utf-8 -*-

from os import PathLike
from typing import Union


class PipeReader:
    def __init__(self, path: Union[str, bytes, PathLike[str], PathLike[bytes]]):
        self._file = open(path, mode="rb")
        assert self._file.readable()
        assert not self._file.writable()

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

    def read(self, n=-1) -> bytes:
        return self._file.read(n)
