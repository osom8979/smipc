# -*- coding: utf-8 -*-

import os
from os import PathLike
from typing import Union

from smipc.pipe.file import PipeFile
from smipc.pipe.flags import get_writer_flags


class PipeWriter(PipeFile):
    def __init__(
        self,
        path: Union[str, bytes, PathLike[str], PathLike[bytes]],
        *,
        blocking=False,
    ):
        super().__init__(path, get_writer_flags(blocking=blocking))

    def write(self, data: bytes) -> int:
        return os.write(self._fd, data)
