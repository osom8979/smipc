# -*- coding: utf-8 -*-

from typing import Final

DEFAULT_PIPE_BUF: Final[int] = 4096
DEFAULT_FILE_MODE: Final[int] = 0o600
DEFAULT_ENCODING: Final[str] = "utf-8"

INFINITY_QUEUE_SIZE: Final[int] = -1

PUB2SUB_SUFFIX: Final[str] = ".p2s.smipc"
SUB2PUB_SUFFIX: Final[str] = ".s2p.smipc"
