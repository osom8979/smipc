# -*- coding: utf-8 -*-

from struct import pack, unpack, unpack_from
from typing import Optional, Sequence


class CudaMemory:
    device_index: int
    device_memory_ptr: int
    device_event_ptr: int
    memory_size: int
    stride: int
    shape: Sequence[int]

    def __init__(
        self,
        device_index: int,
        device_memory_ptr: int,
        device_event_ptr: int,
        memory_size: int,
        stride: Optional[int] = None,
        shape: Optional[Sequence[int]] = None,
    ):
        self.device_index = device_index
        self.device_memory_ptr = device_memory_ptr
        self.device_event_ptr = device_event_ptr
        self.memory_size = memory_size
        self.stride = stride if stride is not None else 0
        self.shape = tuple(shape if shape is not None else ())

    @staticmethod
    def pack_fmt(len_shape: int) -> str:
        # noinspection SpellCheckingInspection
        return f"@IIIIII{len_shape}I"
        # |....| ^       | @ = native byte order
        # |....|  ^      | I = 4 byte unsigned int = device_index
        # |....|   ^     | I = 4 byte unsigned int = device_memory_ptr
        # |....|    ^    | I = 4 byte unsigned int = device_event_ptr
        # |....|     ^   | I = 4 byte unsigned int = memory_size
        # |....|      ^  | I = 4 byte unsigned int = stride
        # |....|       ^ | I = 4 byte unsigned int = len(shape)

    @staticmethod
    def unpack_len_shape(data: bytes) -> int:
        return unpack_from("@I", data, 20)[0]

    def to_bytes(self) -> bytes:
        # noinspection SpellCheckingInspection
        return pack(
            self.pack_fmt(len(self.shape)),
            self.device_index,
            self.device_memory_ptr,
            self.device_event_ptr,
            self.memory_size,
            self.stride,
            len(self.shape),
            *self.shape,
        )

    @classmethod
    def from_bytes(cls, data: bytes):
        len_shape = unpack_from("@I", data, 20)[0]
        fmt = cls.pack_fmt(len_shape)

        props = unpack(fmt, data)
        assert isinstance(props, tuple)
        assert len(props) == 6 + len_shape

        device_index = props[0]
        device_memory_ptr = props[1]
        device_event_ptr = props[2]
        memory_size = props[3]
        stride = props[4]
        assert len_shape == props[5]
        shape = props[6:]

        return cls(
            device_index,
            device_memory_ptr,
            device_event_ptr,
            memory_size,
            stride,
            shape,
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, CudaMemory)
            and self.device_index == other.device_index
            and self.device_memory_ptr == other.device_memory_ptr
            and self.device_event_ptr == other.device_event_ptr
            and self.memory_size == other.memory_size
            and self.stride == other.stride
            and self.shape == other.shape
        )
