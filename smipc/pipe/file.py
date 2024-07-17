# -*- coding: utf-8 -*-

import os
from os import PathLike
from typing import Union

from smipc.pipe.conf import get_pipe_buf


class PipeFile:
    def __init__(
        self,
        path: Union[str, bytes, PathLike[str], PathLike[bytes]],
        flags: int,
    ):
        self._fd = os.open(path, flags)

    def fileno(self) -> int:
        return self._fd

    def close(self) -> None:
        os.close(self._fd)

    @property
    def pipe_buf(self) -> int:
        return get_pipe_buf(self._fd)

    @property
    def blocking(self) -> bool:
        return os.get_blocking(self._fd)

    @blocking.setter
    def blocking(self, value: bool) -> None:
        os.set_blocking(self._fd, value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
