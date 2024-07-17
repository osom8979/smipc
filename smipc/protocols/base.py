# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import NamedTuple, Optional, Tuple

from smipc.decorators.override import override
from smipc.pipe.duplex import FullDuplexPipe
from smipc.pipe.writer import PipeWriter
from smipc.protocols.header import Header, HeaderPacket, Opcode
from smipc.sm.written import SmWritten
from smipc.variables import DEFAULT_ENCODING, DEFAULT_PIPE_BUF


def calc_writer_size(writer: PipeWriter, header: Header) -> int:
    try:
        return writer.pipe_buf - header.size
    except:  # noqa
        return DEFAULT_PIPE_BUF - header.size


class WrittenInfo(NamedTuple):
    pipe_byte: int
    sm_byte: int
    sm_name: Optional[bytes]


class ProtocolInterface(ABC):
    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def send(self, data: bytes) -> WrittenInfo:
        raise NotImplementedError

    @abstractmethod
    def recv(self) -> Optional[bytes]:
        raise NotImplementedError


class SmInterface(ABC):
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


class BaseProtocol(ProtocolInterface, SmInterface, ABC):
    def __init__(
        self,
        pipe: FullDuplexPipe,
        encoding=DEFAULT_ENCODING,
        *,
        force_sm_over_pipe=False,
        disable_restore_sm=False,
    ):
        self._pipe = pipe
        self._encoding = encoding
        self._header = Header()
        self._force_sm_over_pipe = force_sm_over_pipe
        self._disable_restore_sm = disable_restore_sm
        self._writer_size = calc_writer_size(self._pipe.writer, self._header)

    @property
    def pipe(self):
        return self._pipe

    @property
    def header_size(self):
        return self._header.size

    @property
    def encoding(self):
        return self._encoding

    @override
    def close(self) -> None:
        self._pipe.close()
        self.close_sm()

    def send_empty(self) -> WrittenInfo:
        pipe_byte = self._pipe.write(self._header.encode_empty())
        return WrittenInfo(pipe_byte, 0, None)

    def send_pipe_direct(self, data: bytes) -> WrittenInfo:
        header = self._header.encode(Opcode.PIPE_DIRECT, len(data))
        assert len(header) == self._header.size
        pipe_byte = self._pipe.write(header + data)
        return WrittenInfo(pipe_byte, 0, None)

    def send_sm_over_pipe(self, data: bytes) -> WrittenInfo:
        written = self.write_sm(data)
        name = written.encode_name(encoding=self._encoding)
        header = self._header.encode(Opcode.SM_OVER_PIPE, len(name), len(data))
        assert len(header) == self._header.size
        pipe_byte = self._pipe.write(header + name)
        return WrittenInfo(pipe_byte, written.size, name)

    def send_sm_restore(self, sm_name: bytes) -> WrittenInfo:
        header = self._header.encode(Opcode.SM_RESTORE, len(sm_name))
        assert len(header) == self._header.size
        pipe_byte = self._pipe.write(header + sm_name)
        return WrittenInfo(pipe_byte, 0, None)

    @override
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

    def recv_with_header(self) -> Tuple[HeaderPacket, Optional[bytes]]:
        header_data = self._pipe.read(self._header.size)
        header = self._header.decode(header_data)
        if header.opcode == Opcode.EMPTY:
            return header, None
        if header.opcode == Opcode.PIPE_DIRECT:
            return header, self.recv_pipe_direct(header)
        elif header.opcode == Opcode.SM_OVER_PIPE:
            return header, self.recv_sm_over_pipe(header)
        elif header.opcode == Opcode.SM_RESTORE:
            self.recv_sm_restore(header)
            return header, None
        else:
            raise ValueError(f"Unsupported opcode: {header.opcode}")

    @override
    def recv(self) -> Optional[bytes]:
        return self.recv_with_header()[1]
