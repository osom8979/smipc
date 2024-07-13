# -*- coding: utf-8 -*-

import os
from os import PathLike
from pathlib import Path
from threading import Thread
from typing import Optional, Union

from smipc.pipe.reader import PipeReader
from smipc.pipe.writer import PipeWriter


class FullDuplexPipe:
    _writer: PipeWriter
    _reader: PipeReader

    def __init__(
        self,
        writer_path: Union[str, PathLike[str]],
        reader_path: Union[str, PathLike[str]],
        open_timeout: Optional[float] = None,
    ):
        if Path(writer_path) == Path(reader_path):
            raise ValueError("The 'reader_path' and 'writer_path' cannot be the same")

        if not os.path.exists(writer_path):
            raise FileNotFoundError(f"Writer file does not exist: '{writer_path}'")
        if not os.path.exists(reader_path):
            raise FileNotFoundError(f"Reader file does not exist: '{reader_path}'")

        def _create_writer() -> None:
            self._writer = PipeWriter(writer_path)

        def _create_reader() -> None:
            self._reader = PipeReader(reader_path)

        # When opening a FIFO, parallel initialization is required
        # because it is in blocking mode.
        wt = Thread(target=_create_writer, name=f"WriterOpenThread('{writer_path}')")
        rt = Thread(target=_create_reader, name=f"ReaderOpenThread('{reader_path}')")
        wt.start()
        rt.start()
        wt.join(timeout=open_timeout)
        rt.join(timeout=open_timeout)

        assert not self._writer.closed
        assert not self._reader.closed

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

    def flush(self) -> None:
        self._writer.flush()
