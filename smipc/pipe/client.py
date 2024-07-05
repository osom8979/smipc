# -*- coding: utf-8 -*-

from typing import Optional


class PipeClient:
    def __init__(self, read_fifo: Optional[str], write_fifo: Optional[str]):
        pass

    def dequeue(self) -> bytes:
        pass

    def enqueue(self, data: bytes) -> None:
        pass
