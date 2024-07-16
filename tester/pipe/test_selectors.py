# -*- coding: utf-8 -*-

import os
from asyncio import gather, to_thread
from selectors import EVENT_READ, DefaultSelector
from tempfile import TemporaryDirectory
from threading import Event
from typing import Final
from unittest import IsolatedAsyncioTestCase, main, skip

from smipc.pipe.reader import PipeReader
from smipc.pipe.temp import TemporaryPipe
from smipc.pipe.writer import PipeWriter

TEST_TIMEOUT_SECONDS: Final[float] = 0.3


def _read_file(file: PipeReader, size=1) -> bytes:
    return file.read(size)


def _selector_close(selector: DefaultSelector, event: Event) -> None:
    event.wait(TEST_TIMEOUT_SECONDS)
    selector.close()
    event.set()


def _selector_main(selector: DefaultSelector, result: bytearray, event: Event) -> None:
    while not event.is_set():
        try:
            events = selector.select()
        except BaseException as e:
            print(e)
        else:
            if not events:
                continue
            for key, mask in events:
                callback = key.data
                result.extend(callback(key.fileobj))


class SelectorsTestCase(IsolatedAsyncioTestCase):
    def test_default(self):
        with TemporaryDirectory() as tmpdir:
            with TemporaryPipe(os.path.join(tmpdir, "temp.fifo")) as pipe_path:
                reader = PipeReader(pipe_path)
                writer = PipeWriter(pipe_path)

                test_data = b"data"
                self.assertEqual(4, writer.write(test_data))

                selector = DefaultSelector()
                selector.register(reader, EVENT_READ)

                events = selector.select(timeout=TEST_TIMEOUT_SECONDS)
                self.assertEqual(1, len(events))
                key, mask = events[0]
                self.assertEqual(mask, EVENT_READ)
                self.assertIsInstance(key.fileobj, PipeReader)
                self.assertEqual(key.fileobj.fileno(), reader.fileno())
                self.assertEqual(test_data, key.fileobj.read(len(test_data)))

                events = selector.select(timeout=TEST_TIMEOUT_SECONDS)
                self.assertEqual(0, len(events))

                selector.unregister(reader)
                selector.close()

                reader.close()
                writer.close()

    @skip("temporary skip")
    async def test_blocking_interrupt(self):
        with TemporaryDirectory() as tmpdir:
            with TemporaryPipe(os.path.join(tmpdir, "temp.fifo")) as pipe_path:
                reader = PipeReader(pipe_path)
                writer = PipeWriter(pipe_path)

                test_data = b"data"
                self.assertEqual(4, writer.write(test_data))

                selector = DefaultSelector()
                selector.register(reader, EVENT_READ, _read_file)

                result = bytearray()
                event = Event()

                await gather(
                    to_thread(_selector_main, selector, result, event),
                    to_thread(_selector_close, selector, event),
                )
                self.assertEqual(test_data, result)

                selector.unregister(reader)
                selector.close()

                reader.close()
                writer.close()


if __name__ == "__main__":
    main()
