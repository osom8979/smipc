# -*- coding: utf-8 -*-

import os
from asyncio import gather, to_thread
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, main

from smipc.pipe.reader import PipeReader
from smipc.pipe.temp import TemporaryPipe
from smipc.pipe.writer import PipeWriter


class SimplexTestCase(IsolatedAsyncioTestCase):
    async def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))
            file_path = os.path.join(tmpdir, "temp.fifo")
            self.assertFalse(os.path.exists(file_path))
            with TemporaryPipe(file_path) as pipe_path:
                self.assertEqual(file_path, pipe_path)
                self.assertTrue(os.path.exists(pipe_path))

                writer, reader = await gather(
                    to_thread(PipeWriter, pipe_path),
                    to_thread(PipeReader, pipe_path),
                )

                self.assertIsInstance(writer, PipeWriter)
                self.assertIsInstance(reader, PipeReader)

                self.assertFalse(writer.closed)
                self.assertFalse(reader.closed)

                data = b"data"
                self.assertEqual(4, writer.write(data))
                writer.flush()
                self.assertEqual(data, reader.read(4))

                writer.close()
                reader.close()

                self.assertTrue(writer.closed)
                self.assertTrue(reader.closed)

                self.assertTrue(os.path.exists(pipe_path))

            self.assertFalse(os.path.exists(pipe_path))
        self.assertFalse(os.path.exists(tmpdir))


if __name__ == "__main__":
    main()
