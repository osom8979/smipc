# -*- coding: utf-8 -*-

from os import PathLike, pathconf
from typing import Union


def get_pipe_buf(path: Union[int, str, bytes, PathLike[str], PathLike[bytes]]) -> int:
    """Maximum number of bytes guaranteed to be atomic when written to a pipe."""
    return pathconf(path, "PC_PIPE_BUF")  # Availability: Unix.
