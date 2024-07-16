# -*- coding: utf-8 -*-

import os
from os import PathLike
from typing import Final, Union

from smipc.pipe.conf import get_pipe_buf

_BINARY_FLAG: Final[int] = os.O_BINARY if os.name == "nt" else 0
_READER_FLAGS_UNIX: Final[int] = os.O_RDONLY | os.O_NONBLOCK
_READER_FLAGS: Final[int] = _READER_FLAGS_UNIX | _BINARY_FLAG


class PipeReader:
    def __init__(self, path: Union[str, bytes, PathLike[str], PathLike[bytes]]):
        self._fd = os.open(path, _READER_FLAGS)

    def fileno(self) -> int:
        return self._fd

    def close(self) -> None:
        os.close(self._fd)

    def read(self, n: int) -> bytes:
        return os.read(self._fd, n)

    def get_pipe_buf(self) -> int:
        return get_pipe_buf(self._fd)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
