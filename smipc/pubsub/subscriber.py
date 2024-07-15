# -*- coding: utf-8 -*-

import os
from typing import Optional

from smipc.decorators.override import override
from smipc.protocols.base import ProtocolInterface, WrittenInfo
from smipc.protocols.sm import SmProtocol
from smipc.variables import (
    DEFAULT_ENCODING,
    INFINITY_QUEUE_SIZE,
    PUB2SUB_SUFFIX,
    SUB2PUB_SUFFIX,
)


class Subscriber(ProtocolInterface):
    def __init__(
        self,
        prefix: str,
        max_queue=INFINITY_QUEUE_SIZE,
        open_timeout: Optional[float] = None,
        encoding=DEFAULT_ENCODING,
        p2s_suffix=PUB2SUB_SUFFIX,
        s2p_suffix=SUB2PUB_SUFFIX,
    ):
        p2s_path = prefix + p2s_suffix
        s2p_path = prefix + s2p_suffix

        if not os.path.exists(p2s_path):
            raise FileNotFoundError(f"p2s file does not exist: '{p2s_path}'")
        if not os.path.exists(s2p_path):
            raise FileNotFoundError(f"s2p file does not exist: '{s2p_path}'")

        self._proto = SmProtocol.from_fifo(
            reader_path=p2s_path,
            writer_path=s2p_path,
            open_timeout=open_timeout,
            encoding=encoding,
            max_queue=max_queue,
        )

    @override
    def close(self) -> None:
        self._proto.close()

    @override
    def cleanup(self) -> None:
        pass

    @override
    def recv(self) -> Optional[bytes]:
        return self._proto.recv()

    @override
    def send(self, data: bytes) -> WrittenInfo:
        return self._proto.send(data)
