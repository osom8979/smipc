# -*- coding: utf-8 -*-

from io import BufferedReader
from os import PathLike, pathconf
from typing import Union


class PipeReader:
    _file: BufferedReader

    def __init__(self, path: Union[str, bytes, PathLike[str], PathLike[bytes]]):
        self._path = path
        # noinspection PyTypeChecker
        self._file = open(path, mode="rb")
        assert isinstance(self._file, BufferedReader)
        assert self._file.readable()
        assert not self._file.writable()

    @property
    def path(self):
        return self._path

    @property
    def file(self):
        return self._file

    @property
    def closed(self):
        return self._file.closed

    def get_pipe_buf(self) -> int:
        """Maximum number of bytes guaranteed to be atomic when written to a pipe."""
        return pathconf(self._file.fileno(), "PC_PIPE_BUF")  # Availability: Unix.

    def close(self) -> None:
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read(self, n=-1) -> bytes:
        return self._file.read(n)
