# -*- coding: utf-8 -*-

import os
from os import PathLike
from typing import Final, Union

from smipc.pipe.conf import get_pipe_buf

_BINARY_FLAG: Final[int] = os.O_BINARY if os.name == "nt" else 0
_WRITER_FLAGS: Final[int] = os.O_WRONLY | os.O_NONBLOCK | _BINARY_FLAG
_BLOCKING_WRITER_FLAGS: Final[int] = os.O_WRONLY | _BINARY_FLAG


class PipeWriter:
    def __init__(
        self,
        path: Union[str, bytes, PathLike[str], PathLike[bytes]],
        open_blocking=False,
    ):
        if open_blocking:
            self._fd = os.open(path, _BLOCKING_WRITER_FLAGS)
            try:
                os.set_blocking(self._fd, True)
            except:  # noqa
                os.close(self._fd)
                raise
            else:
                assert os.get_blocking(self._fd)
        else:
            self._fd = os.open(path, _WRITER_FLAGS)

    def fileno(self) -> int:
        return self._fd

    def close(self) -> None:
        os.close(self._fd)

    def write(self, data: bytes) -> int:
        return os.write(self._fd, data)

    def get_pipe_buf(self) -> int:
        return get_pipe_buf(self._fd)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
