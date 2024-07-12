# -*- coding: utf-8 -*-

from enum import IntEnum, unique
from struct import Struct, calcsize
from typing import Final, NamedTuple

# noinspection SpellCheckingInspection
HEADER_FORMAT: Final[str] = "@BBHI"
# |........................| ^     | @ = native byte order
# |........................|  ^    | B = 1 byte unsigned char = opcode
# |........................|   ^   | B = 1 byte unsigned char = reserve
# |........................|    ^  | H = 2 byte unsigned short = pipe name size
# |........................|     ^ | I = 4 byte unsigned int = sm buffer size

HEADER_SIZE: Final[int] = calcsize(HEADER_FORMAT)


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


class Header:
    def __init__(self):
        self._header = Struct(HEADER_FORMAT)
        assert self._header.size == HEADER_SIZE

    @property
    def size(self):
        return self._header.size

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
