# -*- coding: utf-8 -*-

import os
from os import PathLike
from typing import Union

from smipc.pipe.file import PipeFile
from smipc.pipe.flags import get_reader_flags


class PipeReader(PipeFile):
    def __init__(
        self,
        path: Union[str, bytes, PathLike[str], PathLike[bytes]],
        *,
        blocking=False,
    ):
        super().__init__(path, get_reader_flags(blocking=blocking))

    def read(self, n: int) -> bytes:
        return os.read(self._fd, n)
