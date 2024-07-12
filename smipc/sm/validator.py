# -*- coding: utf-8 -*-

from contextlib import contextmanager
from typing import NamedTuple
from uuid import uuid4

from smipc.sm.utils import (
    attach_shared_memory,
    create_shared_memory,
    destroy_shared_memory,
)


class SharedMemoryTestInfo(NamedTuple):
    name: str
    data: str


@contextmanager
def register_shared_memory():
    test_sm_data = uuid4().hex
    test_sm_pass_bytes = bytes.fromhex(test_sm_data)
    sm = create_shared_memory(len(test_sm_pass_bytes))
    test_sm_name = sm.name

    try:
        sm.buf[:] = test_sm_pass_bytes
        yield SharedMemoryTestInfo(test_sm_name, test_sm_data)
    finally:
        destroy_shared_memory(sm)


def validate_shared_memory(name: str, data: str) -> bool:
    if name and data:
        try:
            with attach_shared_memory(name) as sm:
                return bytes(sm.buf[:]) == bytes.fromhex(data)
        except:  # noqa
            pass
    return False
