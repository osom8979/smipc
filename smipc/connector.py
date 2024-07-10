# -*- coding: utf-8 -*-

from enum import IntEnum, unique
from warnings import warn
from dataclasses import dataclass
from os import PathLike, pathconf
from struct import Struct
from typing import Final, List, NamedTuple, Optional, Union

from smipc.memory.queue import INFINITY_QUEUE_SIZE, SharedMemoryQueue
from smipc.pipe.duplex import FullDuplexPipe

DEFAULT_PIPE_BUF: Final[int] = 4096


def get_atomic_buffer_size(path: Union[str, PathLike[str]]) -> int:
    """Maximum number of bytes guaranteed to be atomic when written to a pipe."""
    try:
        return pathconf(path, "PC_PIPE_BUF")
    except:  # noqa
        return DEFAULT_PIPE_BUF


@unique
class Opcode(IntEnum):
    PIPE_DIRECT = 0
    SM_OVER_PIPE = 1
    SM_RESTORE = 2


class HeaderPacket(NamedTuple):
    opcode: Opcode
    reserve: int
    pipe_data_size: int
    sm_data_size: int


@dataclass
class ZombieSm:
    name: str
    error: BaseException


class SmipcConnector:
    _zombies: List[ZombieSm]

    def __init__(
        self,
        reader_path: Union[str, PathLike[str]],
        writer_path: Union[str, PathLike[str]],
        max_queue=INFINITY_QUEUE_SIZE,
        open_timeout: Optional[float] = None,
        encoding="utf-8",
    ):
        self._sms = SharedMemoryQueue(max_queue)
        self._pipe = FullDuplexPipe(writer_path, reader_path, open_timeout)
        self._encoding = encoding

        # noinspection SpellCheckingInspection
        self._header = Struct("@BBII")
        # |..................| ^     | @ = native byte order
        # |..................|  ^    | B = 1 byte unsigned char = opcode
        # |..................|   ^   | B = 1 byte unsigned char = reserve
        # |..................|    ^  | I = 2 byte unsigned int = pipe name size
        # |..................|     ^ | I = 4 byte unsigned int = sm buffer size
        assert self._header.size == 8

        self._reader_size = get_atomic_buffer_size(reader_path) - self._header.size
        self._writer_size = get_atomic_buffer_size(writer_path) - self._header.size
        self._zombies = list()

    @property
    def zombies(self) -> List[ZombieSm]:
        return self._zombies.copy()

    def clear_zombies(self) -> None:
        self._zombies.clear()

    def header_pack(self, op: Opcode, pipe_data_size: int, sm_data_size=0) -> bytes:
        return self._header.pack(op, 0x00, pipe_data_size, sm_data_size)

    def header_unpack(self, data: bytes) -> HeaderPacket:
        header = self._header.unpack(data)
        assert isinstance(header, tuple)
        assert len(header) == 4
        opcode = header[0]
        reserve = header[1]
        pipe_data_size = header[2]
        sm_data_size = header[3]
        assert isinstance(opcode, int)
        assert isinstance(reserve, int)
        assert isinstance(pipe_data_size, int)
        assert isinstance(sm_data_size, int)
        return HeaderPacket(
            opcode=Opcode(opcode),
            reserve=reserve,
            pipe_data_size=pipe_data_size,
            sm_data_size=sm_data_size,
        )

    def _send_restore(self, sm_name: str) -> int:
        name = sm_name.encode(encoding=self._encoding)
        header = self.header_pack(Opcode.SM_RESTORE, len(name))
        return self._pipe.write(header + name)

    def _send_pipe_direct(self, data: bytes) -> int:
        header = self.header_pack(Opcode.PIPE_DIRECT, len(data))
        return self._pipe.write(header + data)

    def _send_sm_over_pipe(self, data: bytes) -> int:
        written = self._sms.write(data)
        name = written.name.encode(encoding=self._encoding)
        header = self.header_pack(Opcode.SM_OVER_PIPE, len(name), len(data))
        return self._pipe.write(header + name)

    def send(self, data: bytes) -> int:
        if len(data) <= self._writer_size:
            return self._send_pipe_direct(data)
        else:
            return self._send_sm_over_pipe(data)

    def recv(self) -> Optional[bytes]:
        header_data = self._pipe.read(self._header.size)
        header = self.header_unpack(header_data)

        if header.opcode == Opcode.PIPE_DIRECT:
            assert header.pipe_data_size >= 1
            assert header.sm_data_size == 0
            return self._pipe.read(header.pipe_data_size)

        elif header.opcode == Opcode.SM_OVER_PIPE:
            assert header.pipe_data_size >= 1
            assert header.sm_data_size >= 1
            name = str(self._pipe.read(header.pipe_data_size), encoding=self._encoding)
            result = SharedMemoryQueue.read(name, size=header.sm_data_size)
            assert len(result) == header.sm_data_size
            try:
                self._send_restore(name)
            except BaseException as e:
                warn(
                    f"Shared Memory that could not be returned occurred: '{e}'",
                    ResourceWarning,
                )
                self._zombies.append(ZombieSm(name, e))
            finally:
                return result

        elif header.opcode == Opcode.SM_RESTORE:
            assert header.pipe_data_size >= 1
            assert header.sm_data_size == 0
            name = str(self._pipe.read(header.pipe_data_size), encoding=self._encoding)
            self._sms.restore(name)
            return None

        else:
            raise ValueError(f"Unsupported opcode: {header.opcode}")
