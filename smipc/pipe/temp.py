# -*- coding: utf-8 -*-

import os
from os import PathLike
from typing import Union
from weakref import finalize

from smipc.variables import DEFAULT_FILE_MODE


class TemporaryPipe:
    def __init__(
        self,
        path: Union[str, bytes, PathLike[str], PathLike[bytes]],
        mode=DEFAULT_FILE_MODE,
    ):
        os.mkfifo(path, mode)
        self._path = path
        self._finalizer = finalize(self, self._cleanup, path)

    @staticmethod
    def _cleanup(path: Union[str, bytes, PathLike[str], PathLike[bytes]]) -> None:
        if os.path.exists(path):
            os.remove(path)

    @property
    def path(self):
        return self._path

    def cleanup(self):
        if self._finalizer.detach():
            self._cleanup(self._path)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self._path)

    def __enter__(self):
        return self._path

    def __exit__(self, exc, value, tb):
        self.cleanup()
