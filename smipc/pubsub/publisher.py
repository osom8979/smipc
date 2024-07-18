# -*- coding: utf-8 -*-

import os
from threading import Event
from typing import Optional

from smipc.decorators.override import override
from smipc.pipe.temp import TemporaryPipe
from smipc.protocols.base import ProtocolInterface, WrittenInfo
from smipc.protocols.sm import SmProtocol
from smipc.variables import (
    CLIENT_TO_SERVER_SUFFIX,
    DEFAULT_ENCODING,
    DEFAULT_FILE_MODE,
    INFINITY_QUEUE_SIZE,
    SERVER_TO_CLIENT_SUFFIX,
)


class Publisher(ProtocolInterface):
    def __init__(
        self,
        prefix: str,
        open_timeout: Optional[float] = None,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
        p2s_suffix=SERVER_TO_CLIENT_SUFFIX,
        s2p_suffix=CLIENT_TO_SERVER_SUFFIX,
        mode=DEFAULT_FILE_MODE,
        *,
        interval=0.001,
        blocking: Optional[Event] = None,
    ):
        p2s_path = prefix + p2s_suffix
        s2p_path = prefix + s2p_suffix

        if os.path.exists(p2s_path):
            raise FileExistsError(f"p2s file already exists: '{p2s_path}'")
        if os.path.exists(s2p_path):
            raise FileExistsError(f"s2p file already exists: '{s2p_path}'")

        self._p2s = TemporaryPipe(p2s_path, mode=mode)
        self._s2p = TemporaryPipe(s2p_path, mode=mode)
        assert self._p2s.path == p2s_path
        assert self._s2p.path == s2p_path
        assert os.path.exists(p2s_path)
        assert os.path.exists(s2p_path)

        self._proto = SmProtocol.from_fifo(
            reader_path=s2p_path,
            writer_path=p2s_path,
            open_timeout=open_timeout,
            encoding=encoding,
            max_queue=max_queue,
            interval=interval,
            blocking=blocking,
        )

    def cleanup(self) -> None:
        self._p2s.cleanup()
        self._s2p.cleanup()

    @override
    def close(self) -> None:
        self._proto.close()

    @override
    def recv(self) -> Optional[bytes]:
        return self._proto.recv()

    @override
    def send(self, data: bytes) -> WrittenInfo:
        return self._proto.send(data)
