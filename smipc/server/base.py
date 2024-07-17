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
        s2c_suffix: str,
        c2s_suffix: str,
        mode: int,
    ):
        if s2c_suffix == c2s_suffix:
            raise ValueError("The 's2c_suffix' and 'c2s_suffix' cannot be the same")

        s2c_path = prefix + s2c_suffix
        c2s_path = prefix + c2s_suffix

        if os.path.exists(s2c_path):
            raise FileExistsError(f"s2c file already exists: '{s2c_path}'")
        if os.path.exists(c2s_path):
            raise FileExistsError(f"c2s file already exists: '{c2s_path}'")

        self._key = key
        self._encoding = encoding
        self._max_queue = max_queue
        self._s2c = TemporaryPipe(s2c_path, mode=mode)
        self._c2s = TemporaryPipe(c2s_path, mode=mode)
        assert self._s2c.path == s2c_path
        assert self._c2s.path == c2s_path
        assert os.path.exists(s2c_path)
        assert os.path.exists(c2s_path)

        # ------------------------------------------------------
        # [WARNING] Do not change the calling order.
        reader = PipeReader(c2s_path, blocking=False)

        _fake_writer_reader = PipeReader(s2c_path, blocking=False)
        try:
            writer = PipeWriter(s2c_path, blocking=False)
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
        self._s2c.cleanup()
        self._c2s.cleanup()

    def recv_with_header(self):
        return self._proto.recv_with_header()

    def recv(self):
        return self._proto.recv()

    def send(self, data: bytes):
        return self._proto.send(data)

    def create_client_proto(self, blocking=False):
        reader = PipeReader(self._s2c.path, blocking=blocking)
        writer = PipeWriter(self._c2s.path, blocking=blocking)
        pipe = FullDuplexPipe(writer, reader)
        return SmProtocol(pipe, encoding=self._encoding, max_queue=self._max_queue)


class BaseServer:
    _channels: Dict[str, Channel]

    def __init__(
        self,
        root: str,
        mode=DEFAULT_FILE_MODE,
        *,
        s2c_suffix=PUB2SUB_SUFFIX,
        c2s_suffix=SUB2PUB_SUFFIX,
        make_root=True,
    ):
        if s2c_suffix == c2s_suffix:
            raise ValueError("The 's2c_suffix' and 'c2s_suffix' cannot be the same")

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
        self._s2c_suffix = s2c_suffix
        self._c2s_suffix = c2s_suffix
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
    ):
        if key in self._channels:
            raise KeyError(f"Already opened publisher: '{key}'")
        channel = Channel(
            key=key,
            prefix=self.get_prefix(key),
            encoding=encoding,
            max_queue=max_queue,
            s2c_suffix=self._s2c_suffix,
            c2s_suffix=self._c2s_suffix,
            mode=self._mode,
        )
        self._channels[key] = channel
        return channel

    def close(self, key: str) -> None:
        self._channels[key].close()

    def cleanup(self, key: str) -> None:
        self._channels[key].cleanup()

    def recv_with_header(self, key: str):
        return self._channels[key].recv_with_header()

    def recv(self, key: str):
        return self._channels[key].recv()

    def send(self, key: str, data: bytes):
        return self._channels[key].send(data)
