# -*- coding: utf-8 -*-

from enum import IntEnum, unique
from os import PathLike, pathconf
from struct import Struct
from typing import NamedTuple, Optional, Union

from smipc.memory.queue import SharedMemoryQueue
from smipc.pipe.duplex import FullDuplexPipe
from smipc.variables import DEFAULT_PIPE_BUF, INFINITY_QUEUE_SIZE


def get_atomic_buffer_size(
    path: Union[str, PathLike[str]],
    default=DEFAULT_PIPE_BUF,
) -> int:
    """Maximum number of bytes guaranteed to be atomic when written to a pipe."""
    try:
        return pathconf(path, "PC_PIPE_BUF")  # Availability: Unix.
    except:  # noqa
        return default


@unique
class Opcode(IntEnum):
    PIPE_DIRECT = 0
    SM_OVER_PIPE = 1
    SM_RESTORE = 2


class WrittenInfo(NamedTuple):
    pipe_byte: int
    sm_byte: int
    sm_name: Optional[bytes]


class HeaderPacket(NamedTuple):
    opcode: Opcode
    reserve: int
    pipe_data_size: int
    sm_data_size: int


class SmipcProtocol:
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
        self._header = Struct("@BBHI")
        # |..................| ^     | @ = native byte order
        # |..................|  ^    | B = 1 byte unsigned char = opcode
        # |..................|   ^   | B = 1 byte unsigned char = reserve
        # |..................|    ^  | H = 2 byte unsigned short = pipe name size
        # |..................|     ^ | I = 4 byte unsigned int = sm buffer size
        assert self._header.size == 8

        self._writer_size = get_atomic_buffer_size(writer_path) - self._header.size

    @property
    def header_size(self) -> int:
        return self._header.size

    def close(self) -> None:
        self._pipe.close()
        self._sms.clear()

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

    def _send_pipe_direct(self, data: bytes) -> WrittenInfo:
        header = self.header_pack(Opcode.PIPE_DIRECT, len(data))
        assert len(header) == self._header.size
        pipe_byte = self._pipe.write(header + data)
        self._pipe.flush()
        return WrittenInfo(pipe_byte, 0, None)

    def _send_sm_over_pipe(self, data: bytes) -> WrittenInfo:
        written = self._sms.write(data)
        name = written.name.encode(encoding=self._encoding)
        header = self.header_pack(Opcode.SM_OVER_PIPE, len(name), len(data))
        assert len(header) == self._header.size
        pipe_byte1 = self._pipe.write(header)
        pipe_byte2 = self._pipe.write(name)
        self._pipe.flush()
        sm_byte = written.size
        return WrittenInfo(pipe_byte1 + pipe_byte2, sm_byte, name)

    def _send_sm_restore(self, sm_name: bytes) -> WrittenInfo:
        header = self.header_pack(Opcode.SM_RESTORE, len(sm_name))
        assert len(header) == self._header.size
        pipe_byte1 = self._pipe.write(header)
        pipe_byte2 = self._pipe.write(sm_name)
        self._pipe.flush()
        return WrittenInfo(pipe_byte1 + pipe_byte2, 0, None)

    def send(self, data: bytes) -> WrittenInfo:
        if len(data) <= self._writer_size:
            return self._send_pipe_direct(data)
        else:
            return self._send_sm_over_pipe(data)

    def _recv_pipe_direct(self, header: HeaderPacket) -> bytes:
        assert header.pipe_data_size >= 1
        assert header.sm_data_size == 0
        return self._pipe.read(header.pipe_data_size)

    def _recv_sm_over_pipe(self, header: HeaderPacket) -> bytes:
        assert header.pipe_data_size >= 1
        assert header.sm_data_size >= 1
        sm_name = self._pipe.read(header.pipe_data_size)
        name = str(sm_name, encoding=self._encoding)
        result = SharedMemoryQueue.read(name, size=header.sm_data_size)
        assert len(result) == header.sm_data_size
        restore_result = self._send_sm_restore(sm_name)
        assert restore_result.pipe_byte == self._header.size + len(sm_name)
        assert restore_result.sm_byte == 0
        assert restore_result.sm_name is None
        return result

    def _recv_sm_restore(self, header: HeaderPacket) -> None:
        assert header.pipe_data_size >= 1
        assert header.sm_data_size == 0
        name = str(self._pipe.read(header.pipe_data_size), encoding=self._encoding)
        self._sms.restore(name)

    def recv(self) -> Optional[bytes]:
        header_data = self._pipe.read(self._header.size)
        header = self.header_unpack(header_data)
        if header.opcode == Opcode.PIPE_DIRECT:
            return self._recv_pipe_direct(header)
        elif header.opcode == Opcode.SM_OVER_PIPE:
            return self._recv_sm_over_pipe(header)
        elif header.opcode == Opcode.SM_RESTORE:
            self._recv_sm_restore(header)
            return None
        else:
            raise ValueError(f"Unsupported opcode: {header.opcode}")
