# -*- coding: utf-8 -*-

from functools import lru_cache
from struct import calcsize, pack, unpack_from
from typing import Any, Final, Optional, Sequence

from smipc.cuda.dtype import deserialize_dtype, serialize_dtype

BYTE_ORDER: Final[str] = "@"
# @ = native byte order

# noinspection SpellCheckingInspection
HEADER_FMT: Final[str] = "IIIIIII"
# |.....................| ^       | I =  0 ~ 4 byte unsigned int = device_index
# |.....................|  ^      | I =  4 ~ 4 byte unsigned int = len(event_handle)
# |.....................|   ^     | I =  8 ~ 4 byte unsigned int = len(memory_handle)
# |.....................|    ^    | I = 12 ~ 4 byte unsigned int = len(shape)
# |.....................|     ^   | I = 16 ~ 4 byte unsigned int = stride
# |.....................|      ^  | I = 20 ~ 4 byte unsigned int = memory size
# |.....................|       ^ | I = 24 ~ 4 byte unsigned int = dtype index

DEVICE_INDEX_OFFSET: Final[int] = 0
LEN_EVENT_HANDLE_OFFSET: Final[int] = 4
LEN_MEMORY_HANDLE_OFFSET: Final[int] = 8
LEN_SHAPE_OFFSET: Final[int] = 12
STRIDE_OFFSET: Final[int] = 16
MEMORY_SIZE_OFFSET: Final[int] = 20
DTYPE_INDEX_OFFSET: Final[int] = 24
DATA_OFFSET: Final[int] = 28


def header_fmt(byte_order=True) -> str:
    return f"{BYTE_ORDER}{HEADER_FMT}" if byte_order else HEADER_FMT


@lru_cache()
def header_bytes() -> int:
    return calcsize(header_fmt(byte_order=True))


def data_fmt(
    len_event_handle: int,
    len_memory_handle: int,
    len_shape: int,
    byte_order=True,
) -> str:
    fmt = f"{len_event_handle}s{len_memory_handle}s{len_shape}I"
    return f"{BYTE_ORDER}{fmt}" if byte_order else fmt


def pack_fmt(
    len_event_handle: int,
    len_memory_handle: int,
    len_shape: int,
    byte_order=True,
) -> str:
    header = header_fmt(byte_order=False)
    data = data_fmt(len_event_handle, len_memory_handle, len_shape, byte_order=False)
    fmt = f"{header}{data}"
    return f"{BYTE_ORDER}{fmt}" if byte_order else fmt


class CudaIpcPacket:
    device_index: int
    event_handle: bytes
    memory_handle: bytes
    shape: Sequence[int]
    memory_size: int
    dtype: Any
    stride: int

    def __init__(
        self,
        device_index: int,
        event_handle: bytes,
        memory_handle: bytes,
        memory_size: int,
        dtype: Any,
        stride=0,
        shape: Optional[Sequence[int]] = None,
    ):
        self.device_index = device_index
        self.event_handle = event_handle
        self.memory_handle = memory_handle
        self.shape = tuple(shape if shape is not None else ())
        self.memory_size = memory_size
        self.dtype = dtype
        self.stride = stride

    def to_bytes(self) -> bytes:
        fmt = pack_fmt(
            len_event_handle=len(self.event_handle),
            len_memory_handle=len(self.memory_handle),
            len_shape=len(self.shape),
            byte_order=True,
        )

        # noinspection SpellCheckingInspection
        return pack(
            fmt,
            self.device_index,
            len(self.event_handle),
            len(self.memory_handle),
            len(self.shape),
            self.memory_size,
            serialize_dtype(self.dtype),
            self.stride,
            self.event_handle,
            self.memory_handle,
            *self.shape,
        )

    @classmethod
    def from_bytes(cls, data: bytes):
        header_props = unpack_from(header_fmt(byte_order=True), data)
        assert isinstance(header_props, tuple)
        assert len(header_props) == 7

        device_index = header_props[0]
        len_event_handle = header_props[1]
        len_memory_handle = header_props[2]
        len_shape = header_props[3]
        memory_size = header_props[4]
        dtype_index = header_props[5]
        stride = header_props[6]

        fmt = data_fmt(len_event_handle, len_memory_handle, len_shape, byte_order=True)
        data_props = unpack_from(fmt, data, offset=DATA_OFFSET)
        assert isinstance(data_props, tuple)
        assert len(data_props) == 2 + len_shape

        event_handle = data_props[0]
        memory_handle = data_props[1]
        shape = data_props[2:]

        assert isinstance(event_handle, bytes)
        assert len(event_handle) == len_event_handle
        assert isinstance(memory_handle, bytes)
        assert len(memory_handle) == len_memory_handle
        assert isinstance(shape, tuple)
        assert len(shape) == len_shape

        return cls(
            device_index,
            event_handle,
            memory_handle,
            memory_size,
            deserialize_dtype(dtype_index),
            stride,
            shape,
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, CudaIpcPacket)
            and self.device_index == other.device_index
            and self.memory_handle == other.memory_handle
            and self.event_handle == other.event_handle
            and self.shape == other.shape
            and self.memory_size == other.memory_size
            and self.dtype == other.dtype
            and self.stride == other.stride
        )
