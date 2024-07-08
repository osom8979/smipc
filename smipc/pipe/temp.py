# -*- coding: utf-8 -*-

from io import BufferedWriter
from os import PathLike, mkfifo, pathconf, remove
from typing import Union
from weakref import finalize


class TemporaryPipe:
    _file: BufferedWriter

    def __init__(
        self,
        path: Union[str, bytes, PathLike[str], PathLike[bytes]],
        mode=0o666,
    ):
        mkfifo(path, mode)
        self._path = path
        self._finalizer = finalize(self, self._cleanup, path)

    @staticmethod
    def _cleanup(path: Union[str, bytes, PathLike[str], PathLike[bytes]]) -> None:
        remove(path)

    @property
    def path(self):
        return self._path

    @property
    def pipe_buffer_size(self):
        return pathconf(self._path, "PC_PIPE_BUF")

    def cleanup(self):
        if self._finalizer.detach():
            self._cleanup(self._path)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self._path)

    def __enter__(self):
        return self._path

    def __exit__(self, exc, value, tb):
        self.cleanup()
