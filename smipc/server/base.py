# -*- coding: utf-8 -*-

import os
from abc import ABC, abstractmethod
from typing import Dict, NamedTuple, Optional
from weakref import ReferenceType, ref

from smipc.decorators.override import override
from smipc.pipe.duplex import FullDuplexPipe
from smipc.pipe.reader import PipeReader
from smipc.pipe.temp_pair import TemporaryPipePair
from smipc.pipe.writer import PipeWriter
from smipc.protocols.sm import SmProtocol
from smipc.variables import (
    CLIENT_TO_SERVER_SUFFIX,
    DEFAULT_ENCODING,
    DEFAULT_FILE_MODE,
    INFINITY_QUEUE_SIZE,
    SERVER_TO_CLIENT_SUFFIX,
)


class PathPair(NamedTuple):
    s2c: str
    c2s: str


def get_prefix(root: str, key: str) -> str:
    return os.path.join(root, key)


def get_path_pair(
    root: str,
    key: str,
    flip=False,
    s2c_suffix=SERVER_TO_CLIENT_SUFFIX,
    c2s_suffix=CLIENT_TO_SERVER_SUFFIX,
) -> PathPair:
    prefix = get_prefix(root, key)
    s2c_path = prefix + s2c_suffix
    c2s_path = prefix + c2s_suffix
    if flip:
        return PathPair(c2s_path, s2c_path)
    else:
        return PathPair(s2c_path, c2s_path)


def create_fifos(paths: PathPair, mode=DEFAULT_FILE_MODE):
    s2c_path = paths.s2c
    c2s_path = paths.c2s
    return TemporaryPipePair(s2c_path, c2s_path, mode)


def create_pipe(paths: PathPair, blocking=False, *, no_faker=False):
    s2c_path = paths.s2c
    c2s_path = paths.c2s

    if not os.path.exists(s2c_path):
        raise FileNotFoundError(f"s2c file does not exist: '{s2c_path}'")
    if not os.path.exists(c2s_path):
        raise FileNotFoundError(f"c2s file does not exist: '{c2s_path}'")

    # ------------------------------------------------------
    # [WARNING] Do not change the calling order.
    reader = PipeReader(c2s_path, blocking=blocking)

    _fake_writer_reader = None if no_faker else PipeReader(s2c_path, blocking=False)
    try:
        writer = PipeWriter(s2c_path, blocking=blocking)
    except:  # noqa
        raise
    finally:
        if _fake_writer_reader is not None:
            _fake_writer_reader.close()
    # ------------------------------------------------------

    return FullDuplexPipe(writer, reader)


def create_proto(
    pipe: FullDuplexPipe,
    encoding=DEFAULT_ENCODING,
    max_queue=INFINITY_QUEUE_SIZE,
):
    return SmProtocol(
        pipe=pipe,
        encoding=encoding,
        max_queue=max_queue,
    )


class Channel:
    def __init__(
        self,
        key: str,
        proto: SmProtocol,
        weak_base: Optional[ReferenceType["BaseServer"]] = None,
        fifos: Optional[TemporaryPipePair] = None,
    ):
        self._key = key
        self._proto = proto
        self._weak_base = weak_base
        self._fifos = fifos

    @property
    def key(self):
        return self._key

    @property
    def proto(self):
        return self._proto

    @property
    def reader(self):
        return self._proto.pipe.reader

    @property
    def writer(self):
        return self._proto.pipe.writer

    @property
    def base(self):
        if self._weak_base is None:
            return None
        else:
            return self._weak_base()

    def close(self) -> None:
        self._proto.close()

    def cleanup(self) -> None:
        if self._fifos is not None:
            self._fifos.cleanup()

    def recv_with_header(self):
        return self._proto.recv_with_header()

    def recv(self):
        return self._proto.recv()

    def send(self, data: bytes):
        return self._proto.send(data)


class BaseClient(Channel):
    def __init__(self, key: str, proto: SmProtocol):
        super().__init__(key, proto)

    @classmethod
    def from_channel(cls, channel: Channel):
        if channel._weak_base is not None:
            raise ValueError("The 'weak_base' attribute of the channel is already set")
        if channel._fifos is not None:
            raise ValueError("The 'fifos' attribute of the channel is already set")

        return cls(channel.key, channel.proto)

    @classmethod
    def from_root(
        cls,
        root: str,
        key: str,
        blocking=False,
        *,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
        s2c_suffix=SERVER_TO_CLIENT_SUFFIX,
        c2s_suffix=CLIENT_TO_SERVER_SUFFIX,
    ):
        paths = get_path_pair(
            root=root,
            key=key,
            flip=True,
            s2c_suffix=s2c_suffix,
            c2s_suffix=c2s_suffix,
        )
        pipe = create_pipe(paths, blocking=blocking, no_faker=True)
        proto = create_proto(pipe, encoding, max_queue)
        return cls(key, proto)


class BaseServerInterface(ABC):
    @abstractmethod
    def on_create_channel(
        self,
        key: str,
        proto: SmProtocol,
        weak_base: Optional[ReferenceType],
        fifos: Optional[TemporaryPipePair],
    ):
        raise NotImplementedError


class BaseServer(BaseServerInterface):
    _channels: Dict[str, Channel]

    def __init__(
        self,
        root: str,
        mode=DEFAULT_FILE_MODE,
        encoding=DEFAULT_ENCODING,
        max_queue=INFINITY_QUEUE_SIZE,
        *,
        s2c_suffix=SERVER_TO_CLIENT_SUFFIX,
        c2s_suffix=CLIENT_TO_SERVER_SUFFIX,
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
        self._encoding = encoding
        self._max_queue = max_queue
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

    def get_path_pair(self, key: str, flip=False):
        return get_path_pair(
            root=self._root,
            key=key,
            flip=flip,
            s2c_suffix=self._s2c_suffix,
            c2s_suffix=self._c2s_suffix,
        )

    @override
    def on_create_channel(
        self,
        key: str,
        proto: SmProtocol,
        weak_base: Optional[ReferenceType],
        fifos: Optional[TemporaryPipePair],
    ):
        return Channel(key, proto, weak_base, fifos)

    def create_server_channel(self, key: str, blocking=False):
        # ------------------------------------------
        # [WARNING] Do not change the calling order.
        paths = self.get_path_pair(key)
        fifos = create_fifos(paths, self._mode)
        pipe = create_pipe(paths, blocking=blocking, no_faker=False)
        proto = create_proto(pipe, self._encoding, self._max_queue)
        # ------------------------------------------
        return self.on_create_channel(key, proto, ref(self), fifos)

    def create_client_channel(self, key: str, blocking=False):
        paths = self.get_path_pair(key, flip=True)
        pipe = create_pipe(paths, blocking=blocking, no_faker=True)
        proto = create_proto(pipe, self._encoding, self._max_queue)
        return self.on_create_channel(key, proto, None, None)

    def open(self, key: str, blocking=False):
        if key in self._channels:
            raise KeyError(f"Already opened channel: '{key}'")

        channel = self.create_server_channel(key, blocking=blocking)
        self._channels[channel.key] = channel
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
