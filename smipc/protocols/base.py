# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from os import PathLike, pathconf
from typing import NamedTuple, Optional, Union

from smipc.pipe.duplex import FullDuplexPipe
from smipc.protocols.header import Header, HeaderPacket, Opcode
from smipc.sm.written import SmWritten
from smipc.variables import DEFAULT_ENCODING, DEFAULT_PIPE_BUF


def get_atomic_buffer_size(
    path: Union[str, PathLike[str]],
    default=DEFAULT_PIPE_BUF,
) -> int:
    """Maximum number of bytes guaranteed to be atomic when written to a pipe."""
    try:
        return pathconf(path, "PC_PIPE_BUF")  # Availability: Unix.
    except:  # noqa
        return default


class WrittenInfo(NamedTuple):
    pipe_byte: int
    sm_byte: int
    sm_name: Optional[bytes]


class SmProtocolInterface(ABC):
    @abstractmethod
    def close_sm(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def write_sm(self, data: bytes) -> SmWritten:
        raise NotImplementedError

    @abstractmethod
    def read_sm(self, name: bytes, size: int) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def restore_sm(self, name: bytes) -> None:
        raise NotImplementedError


class BaseProtocol(SmProtocolInterface, ABC):
    def __init__(
        self,
        reader_path: Union[str, PathLike[str]],
        writer_path: Union[str, PathLike[str]],
        open_timeout: Optional[float] = None,
        encoding=DEFAULT_ENCODING,
        *,
        force_sm_over_pipe=False,
        disable_restore_sm=False,
    ):
        self._pipe = FullDuplexPipe(writer_path, reader_path, open_timeout)
        self._encoding = encoding
        self._header = Header()
        self._writer_size = get_atomic_buffer_size(writer_path) - self._header.size
        self._force_sm_over_pipe = force_sm_over_pipe
        self._disable_restore_sm = disable_restore_sm

    @property
    def header_size(self):
        return self._header.size

    @property
    def encoding(self):
        return self._encoding

    def close(self) -> None:
        self._pipe.close()
        self.close_sm()

    def send_pipe_direct(self, data: bytes) -> WrittenInfo:
        header = self._header.encode(Opcode.PIPE_DIRECT, len(data))
        assert len(header) == self._header.size
        pipe_byte1 = self._pipe.write(header)
        pipe_byte2 = self._pipe.write(data)
        self._pipe.flush()
        return WrittenInfo(pipe_byte1 + pipe_byte2, 0, None)

    def send_sm_over_pipe(self, data: bytes) -> WrittenInfo:
        written = self.write_sm(data)
        name = written.encode_name(encoding=self._encoding)
        header = self._header.encode(Opcode.SM_OVER_PIPE, len(name), len(data))
        assert len(header) == self._header.size
        pipe_byte1 = self._pipe.write(header)
        pipe_byte2 = self._pipe.write(name)
        self._pipe.flush()
        sm_byte = written.size
        return WrittenInfo(pipe_byte1 + pipe_byte2, sm_byte, name)

    def send_sm_restore(self, sm_name: bytes) -> WrittenInfo:
        header = self._header.encode(Opcode.SM_RESTORE, len(sm_name))
        assert len(header) == self._header.size
        pipe_byte1 = self._pipe.write(header)
        pipe_byte2 = self._pipe.write(sm_name)
        self._pipe.flush()
        return WrittenInfo(pipe_byte1 + pipe_byte2, 0, None)

    def send(self, data: bytes) -> WrittenInfo:
        if not self._force_sm_over_pipe and len(data) <= self._writer_size:
            return self.send_pipe_direct(data)
        else:
            return self.send_sm_over_pipe(data)

    def recv_pipe_direct(self, header: HeaderPacket) -> bytes:
        assert header.pipe_data_size >= 1
        assert header.sm_data_size == 0
        return self._pipe.read(header.pipe_data_size)

    def recv_sm_over_pipe(self, header: HeaderPacket) -> bytes:
        assert header.pipe_data_size >= 1
        assert header.sm_data_size >= 1
        sm_name = self._pipe.read(header.pipe_data_size)
        result = self.read_sm(sm_name, header.sm_data_size)

        if not self._disable_restore_sm:
            restore_result = self.send_sm_restore(sm_name)
            assert restore_result.pipe_byte == self._header.size + len(sm_name)
            assert restore_result.sm_byte == 0
            assert restore_result.sm_name is None

        return result

    def recv_sm_restore(self, header: HeaderPacket) -> None:
        assert header.pipe_data_size >= 1
        assert header.sm_data_size == 0
        name = self._pipe.read(header.pipe_data_size)
        self.restore_sm(name)

    def recv(self) -> Optional[bytes]:
        header_data = self._pipe.read(self._header.size)
        header = self._header.decode(header_data)
        if header.opcode == Opcode.PIPE_DIRECT:
            return self.recv_pipe_direct(header)
        elif header.opcode == Opcode.SM_OVER_PIPE:
            return self.recv_sm_over_pipe(header)
        elif header.opcode == Opcode.SM_RESTORE:
            self.recv_sm_restore(header)
            return None
        else:
            raise ValueError(f"Unsupported opcode: {header.opcode}")
