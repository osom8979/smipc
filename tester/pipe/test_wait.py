# -*- coding: utf-8 -*-

import os
from asyncio import gather, to_thread
from tempfile import TemporaryDirectory
from threading import Event
from typing import Final
from unittest import IsolatedAsyncioTestCase, main

from smipc.pipe.reader import PipeReader
from smipc.pipe.temp import TemporaryPipe
from smipc.pipe.wait import blocking_pipe_writer, wait_pipe_writer

TEST_TIMEOUT_SECONDS: Final[float] = 0.3


def _event_wait(event: Event):
    event.wait(TEST_TIMEOUT_SECONDS)
    event.set()


def _wait_open(path: str, event: Event):
    if event.is_set():
        raise ValueError
    return wait_pipe_writer(path, event=event)


def _blocking_open(path: str, event: Event):
    if event.is_set():
        raise ValueError
    return blocking_pipe_writer(path, event=event)


class WaitTestCase(IsolatedAsyncioTestCase):
    def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))

            file_path = os.path.join(tmpdir, "temp.fifo")
            self.assertFalse(os.path.exists(file_path))

            with TemporaryPipe(file_path) as pipe_path:
                self.assertEqual(file_path, pipe_path)
                self.assertTrue(os.path.exists(pipe_path))

                reader = PipeReader(pipe_path)
                writer = wait_pipe_writer(pipe_path)

                data = b"data"
                self.assertEqual(4, writer.write(data))
                self.assertEqual(data, reader.read(4))

                writer.close()
                reader.close()
                self.assertTrue(os.path.exists(pipe_path))

            self.assertFalse(os.path.exists(pipe_path))
        self.assertFalse(os.path.exists(tmpdir))

    def test_wait_pipe_writer_timeout(self):
        with TemporaryDirectory() as tmpdir:
            with TemporaryPipe(os.path.join(tmpdir, "temp.fifo")) as pipe_path:
                with self.assertRaises(TimeoutError):
                    wait_pipe_writer(pipe_path, timeout=TEST_TIMEOUT_SECONDS)

    def test_blocking_pipe_writer_timeout(self):
        with TemporaryDirectory() as tmpdir:
            with TemporaryPipe(os.path.join(tmpdir, "temp.fifo")) as pipe_path:
                with self.assertRaises(TimeoutError):
                    blocking_pipe_writer(pipe_path, timeout=TEST_TIMEOUT_SECONDS)

    async def test_wait_pipe_writer_interrupt(self):
        with TemporaryDirectory() as tmpdir:
            with TemporaryPipe(os.path.join(tmpdir, "temp.fifo")) as pipe_path:
                event = Event()
                self.assertFalse(event.is_set())

                with self.assertRaises(InterruptedError):
                    await gather(
                        to_thread(_event_wait, event),
                        to_thread(_wait_open, pipe_path, event),
                    )
                self.assertTrue(event.is_set())

    async def test_blocking_pipe_writer_interrupt(self):
        with TemporaryDirectory() as tmpdir:
            with TemporaryPipe(os.path.join(tmpdir, "temp.fifo")) as pipe_path:
                event = Event()
                self.assertFalse(event.is_set())

                with self.assertRaises(InterruptedError):
                    await gather(
                        to_thread(_event_wait, event),
                        to_thread(_blocking_open, pipe_path, event),
                    )
                self.assertTrue(event.is_set())


if __name__ == "__main__":
    main()
