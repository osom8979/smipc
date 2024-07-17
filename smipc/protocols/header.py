# -*- coding: utf-8 -*-

from enum import IntEnum, unique
from struct import Struct, calcsize, pack
from typing import Final, NamedTuple


@unique
class Opcode(IntEnum):
    EMPTY = 0
    """It exists for I/O signaling."""

    PIPE_DIRECT = 1
    """Communication using Named PIPE only."""

    SM_OVER_PIPE = 2
    """Send Shared Memory information to Named PIPE."""

    SM_RESTORE = 3
    """Returns the Shared Memory ownership."""


class HeaderPacket(NamedTuple):
    opcode: Opcode
    reserve: int
    pipe_data_size: int
    sm_data_size: int


# noinspection SpellCheckingInspection
HEADER_FORMAT: Final[str] = "@BBHI"
# |........................| ^     | @ = native byte order
# |........................|  ^    | B = 1 byte unsigned char = opcode
# |........................|   ^   | B = 1 byte unsigned char = reserve
# |........................|    ^  | H = 2 byte unsigned short = pipe name size
# |........................|     ^ | I = 4 byte unsigned int = sm buffer size

HEADER_SIZE: Final[int] = calcsize(HEADER_FORMAT)

EMPTY_HEADER_PACKET: Final[bytes] = pack(HEADER_FORMAT, int(Opcode.EMPTY), 0x00, 0, 0)


class Header:
    def __init__(self):
        self._header = Struct(HEADER_FORMAT)
        assert self._header.size == HEADER_SIZE

    @property
    def size(self):
        return self._header.size

    @staticmethod
    def encode_empty() -> bytes:
        return EMPTY_HEADER_PACKET

    def encode(self, op: Opcode, pipe_data_size: int, sm_data_size=0) -> bytes:
        return self._header.pack(int(op), 0x00, pipe_data_size, sm_data_size)

    def decode(self, data: bytes) -> HeaderPacket:
        props = self._header.unpack(data)
        assert isinstance(props, tuple)
        assert len(props) == 4

        opcode = props[0]
        reserve = props[1]
        pipe_data_size = props[2]
        sm_data_size = props[3]

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
