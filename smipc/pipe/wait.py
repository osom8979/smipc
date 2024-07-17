# -*- coding: utf-8 -*-

import os
from enum import Enum, auto, unique
from errno import ENXIO
from os import PathLike
from threading import Event, Lock, Thread
from time import sleep, time
from typing import Optional, Type, Union

from smipc.pipe.reader import PipeReader
from smipc.pipe.writer import PipeWriter


def wait_exists(
    path: Union[int, str, bytes, PathLike[str], PathLike[bytes]],
    timeout: Optional[float] = None,
    interval=0.001,
    event: Optional[Event] = None,
) -> None:
    if not interval >= 0:
        raise ValueError("'interval' must be a positive float")

    event = event if event is not None else Event()
    assert event is not None

    begin = time()
    while not event.is_set():
        if os.path.exists(path):
            return
        if timeout is not None and (time() - begin) > timeout:
            raise TimeoutError
        sleep(interval)

    assert event.is_set()
    raise InterruptedError


def wait_pipe_writer(
    path: Union[str, bytes, PathLike[str], PathLike[bytes]],
    timeout: Optional[float] = None,
    interval=0.001,
    event: Optional[Event] = None,
) -> PipeWriter:
    if not interval >= 0:
        raise ValueError("'interval' must be a positive float")

    event = event if event is not None else Event()
    assert event is not None

    begin = time()
    while not event.is_set():
        try:
            return PipeWriter(path, blocking=False)
        except OSError as e:
            if e.errno == ENXIO:
                # No such device or address
                if timeout is not None and (time() - begin) > timeout:
                    raise TimeoutError
        sleep(interval)

    assert event.is_set()
    raise InterruptedError


@unique
class _BlockingEndReason(Enum):
    INTERRUPT = auto()
    TIMEOUT = auto()


class _BlockingPipeWriterResult:
    _event: Event
    _writer: Optional[PipeWriter]
    _error: Optional[BaseException]

    def __init__(self, event: Optional[Event] = None):
        self._event = event if event is not None else Event()
        self._lock = Lock()
        self._writer = None
        self._error = None

    def wait(self, timeout: Optional[float] = None) -> bool:
        return self._event.wait(timeout)

    def values(self):
        with self._lock:
            return self._writer, self._error

    def set_writer(self, value: PipeWriter) -> None:
        with self._lock:
            self._writer = value

    def set_error(self, value: BaseException) -> None:
        with self._lock:
            self._error = value

    def set_event(self) -> None:
        self._event.set()


def _blocking_pipe_writer_open(
    path: Union[str, bytes, PathLike[str], PathLike[bytes]],
    result: _BlockingPipeWriterResult,
) -> None:
    try:
        writer = PipeWriter(path, blocking=True)
    except BaseException as e:
        result.set_error(e)
    else:
        result.set_writer(writer)
    finally:
        result.set_event()


def blocking_pipe_writer(
    path: Union[str, bytes, PathLike[str], PathLike[bytes]],
    timeout: Optional[float] = None,
    event: Optional[Event] = None,
    *,
    thread_join_timeout: Optional[float] = 4.0,
) -> PipeWriter:
    result = _BlockingPipeWriterResult(event)

    thread = Thread(
        group=None,
        target=_blocking_pipe_writer_open,
        args=(path, result),
    )
    thread.start()

    end_reason: Union[Type[InterruptedError], Type[TimeoutError]]
    end_error: Optional[BaseException] = None

    if result.wait(timeout=timeout):
        writer, error = result.values()
        if writer is not None:
            # opened successfully
            assert error is None
            thread.join(timeout=thread_join_timeout)
            assert not thread.is_alive()
            return writer
        elif error is not None:
            # raise error
            assert writer is None
            thread.join(timeout=thread_join_timeout)
            assert not thread.is_alive()
            raise error
        else:
            end_reason = InterruptedError
    else:
        end_reason = TimeoutError

    assert end_reason in (InterruptedError, TimeoutError)

    fake_reader = PipeReader(path)
    try:
        # To release a blocking thread...
        thread.join(timeout=thread_join_timeout)
        assert not thread.is_alive()

        writer, error = result.values()
        if writer is not None:
            assert error is None
            writer.close()
        elif error is not None:
            assert writer is None
            end_error = error
    finally:
        fake_reader.close()

    raise end_reason from end_error
