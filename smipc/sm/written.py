# -*- coding: utf-8 -*-

from typing import NamedTuple, Union


class SmWritten(NamedTuple):
    name: Union[str, bytes]
    offset: int
    end: int

    @property
    def size(self) -> int:
        return self.end - self.offset

    def encode_name(self, encoding="utf-8") -> bytes:
        if isinstance(self.name, str):
            return self.name.encode(encoding=encoding)
        else:
            assert isinstance(self.name, bytes)
            return self.name
