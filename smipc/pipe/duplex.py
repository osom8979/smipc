# -*- coding: utf-8 -*-

import os
from os import PathLike
from pathlib import Path
from threading import Event
from typing import Optional, Union

from smipc.pipe.reader import PipeReader
from smipc.pipe.wait import blocking_pipe_writer, wait_pipe_writer
from smipc.pipe.writer import PipeWriter


class FullDuplexPipe:
    _writer: PipeWriter
    _reader: PipeReader

    def __init__(self, writer: PipeWriter, reader: PipeReader):
        self._writer = writer
        self._reader = reader

    @classmethod
    def from_fifo(
        cls,
        writer_path: Union[str, PathLike[str]],
        reader_path: Union[str, PathLike[str]],
        open_timeout: Optional[float] = None,
        *,
        interval=0.001,
        blocking: Optional[Event] = None,
    ):
        if not interval >= 0:
            raise ValueError("The 'interval' must be a positive float")

        if Path(writer_path) == Path(reader_path):
            raise ValueError("The 'reader_path' and 'writer_path' cannot be the same")

        if not os.path.exists(writer_path):
            raise FileNotFoundError(f"Writer file does not exist: '{writer_path}'")
        if not os.path.exists(reader_path):
            raise FileNotFoundError(f"Reader file does not exist: '{reader_path}'")

        # ------------------------------------------------------------
        # [WARNING] Do not change the calling order.
        reader = PipeReader(reader_path, blocking=False)
        try:
            if blocking is not None:
                writer = blocking_pipe_writer(writer_path, open_timeout, blocking)
            else:
                writer = wait_pipe_writer(writer_path, open_timeout, interval)
        except:  # noqa
            reader.close()
            raise
        # ------------------------------------------------------------

        return cls(reader=reader, writer=writer)

    @property
    def writer(self):
        return self._writer

    @property
    def reader(self):
        return self._reader

    def close(self) -> None:
        self._writer.close()
        self._reader.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read(self, n=-1) -> bytes:
        return self._reader.read(n)

    def write(self, data: bytes) -> int:
        return self._writer.write(data)
