# -*- coding: utf-8 -*-

import os
from typing import Dict

from smipc.pipe.duplex import FullDuplexPipe
from smipc.pipe.reader import PipeReader
from smipc.pipe.temp import TemporaryPipe
from smipc.pipe.writer import PipeWriter
from smipc.protocols.sm import SmProtocol
from smipc.variables import (
    DEFAULT_ENCODING,
    DEFAULT_FILE_MODE,
    INFINITY_QUEUE_SIZE,
    PUB2SUB_SUFFIX,
    SUB2PUB_SUFFIX,
)


class Channel:
    def __init__(
        self,
        key: str,
        prefix: str,
        encoding: str,
        max_queue: int,
        p2s_suffix: str,
        s2p_suffix: str,
        mode: int,
    ):
        if p2s_suffix == s2p_suffix:
            raise ValueError("The 'p2s_suffix' and 's2p_suffix' cannot be the same")

        p2s_path = prefix + p2s_suffix
        s2p_path = prefix + s2p_suffix

        if os.path.exists(p2s_path):
            raise FileExistsError(f"p2s file already exists: '{p2s_path}'")
        if os.path.exists(s2p_path):
            raise FileExistsError(f"s2p file already exists: '{s2p_path}'")

        self._key = key
        self._p2s = TemporaryPipe(p2s_path, mode=mode)
        self._s2p = TemporaryPipe(s2p_path, mode=mode)
        assert self._p2s.path == p2s_path
        assert self._s2p.path == s2p_path
        assert os.path.exists(p2s_path)
        assert os.path.exists(s2p_path)

        # ------------------------------------------------------
        # [WARNING] Do not change the calling order.
        reader = PipeReader(s2p_path, blocking=False)

        _fake_writer_reader = PipeReader(p2s_path, blocking=False)
        try:
            writer = PipeWriter(p2s_path, blocking=False)
        finally:
            _fake_writer_reader.close()
        # ------------------------------------------------------

        self._proto = SmProtocol(FullDuplexPipe(writer, reader), encoding, max_queue)

    @property
    def key(self):
        return self._key

    @property
    def reader(self):
        return self._proto.pipe.reader

    @property
    def writer(self):
        return self._proto.pipe.writer

    def close(self) -> None:
        self._proto.close()

    def cleanup(self) -> None:
        self._p2s.cleanup()
        self._s2p.cleanup()

    def recv(self):
        return self._proto.recv_with_header()

    def send(self, data: bytes):
        return self._proto.send(data)


class BaseServer:
    _channels: Dict[str, Channel]

    def __init__(
        self,
        root: str,
        mode=DEFAULT_FILE_MODE,
        *,
        p2s_suffix=PUB2SUB_SUFFIX,
        s2p_suffix=SUB2PUB_SUFFIX,
        make_root=True,
    ):
        if p2s_suffix == s2p_suffix:
            raise ValueError("The 'p2s_suffix' and 's2p_suffix' cannot be the same")

        if make_root:
            if os.path.exists(root):
                if not os.path.isdir(root):
                    raise FileExistsError(f"'{root}' is not a directory")
            else:
                os.mkdir(root, mode)

        if not os.path.isdir(root):
            raise NotADirectoryError(f"'{root}' must be a directory")

        self._root = root
        self._mode = mode
        self._p2s_suffix = p2s_suffix
        self._s2p_suffix = s2p_suffix
        self._channels = dict()

    @property
    def root(self):
        return self._root

    def __getitem__(self, key: str):
        return self._channels.__getitem__(key)

    def __len__(self) -> int:
        return self._channels.__len__()

    def keys(self):
        return self._channels.keys()

    def values(self):
        return self._channels.values()

    def get_prefix(self, key: str) -> str:
        return os.path.join(self._root, key)

    def open(
        self,
        key: str,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
    ) -> None:
        if key in self._channels:
            raise KeyError(f"Already opened publisher: '{key}'")
        self._channels[key] = Channel(
            key=key,
            prefix=self.get_prefix(key),
            encoding=encoding,
            max_queue=max_queue,
            p2s_suffix=self._p2s_suffix,
            s2p_suffix=self._s2p_suffix,
            mode=self._mode,
        )

    def close(self, key: str) -> None:
        self._channels[key].close()

    def cleanup(self, key: str) -> None:
        self._channels[key].cleanup()

    def recv(self, key: str):
        return self._channels[key].recv()

    def send(self, key: str, data: bytes):
        return self._channels[key].send(data)
