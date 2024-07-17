# -*- coding: utf-8 -*-

import os
from typing import Final

BINARY_FLAG: Final[int] = os.O_BINARY if os.name == "nt" else 0

BLOCKING_READER_FLAGS: Final[int] = BINARY_FLAG | os.O_RDONLY
NONBLOCK_READER_FLAGS: Final[int] = BINARY_FLAG | os.O_RDONLY | os.O_NONBLOCK

BLOCKING_WRITER_FLAGS: Final[int] = BINARY_FLAG | os.O_WRONLY
NONBLOCK_WRITER_FLAGS: Final[int] = BINARY_FLAG | os.O_WRONLY | os.O_NONBLOCK


def get_reader_flags(blocking: bool) -> int:
    if blocking:
        return BLOCKING_READER_FLAGS
    else:
        return NONBLOCK_READER_FLAGS


def get_writer_flags(blocking: bool) -> int:
    if blocking:
        return BLOCKING_WRITER_FLAGS
    else:
        return NONBLOCK_WRITER_FLAGS
