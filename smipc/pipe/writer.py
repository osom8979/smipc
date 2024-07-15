# -*- coding: utf-8 -*-

from io import BufferedWriter
from os import PathLike, pathconf
from typing import Union


class PipeWriter:
    _file: BufferedWriter

    def __init__(self, path: Union[str, bytes, PathLike[str], PathLike[bytes]]):
        self._path = path
        # noinspection PyTypeChecker
        self._file = open(path, mode="wb")
        assert isinstance(self._file, BufferedWriter)
        assert not self._file.readable()
        assert self._file.writable()

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

    def write(self, data: bytes) -> int:
        return self._file.write(data)

    def flush(self) -> None:
        self._file.flush()
