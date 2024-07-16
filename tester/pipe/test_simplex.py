# -*- coding: utf-8 -*-

import os
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from smipc.pipe.reader import PipeReader
from smipc.pipe.temp import TemporaryPipe
from smipc.pipe.writer import PipeWriter


class SimplexTestCase(TestCase):
    def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))

            file_path = os.path.join(tmpdir, "temp.fifo")
            self.assertFalse(os.path.exists(file_path))

            with TemporaryPipe(file_path) as pipe_path:
                self.assertEqual(file_path, pipe_path)
                self.assertTrue(os.path.exists(pipe_path))

                reader = PipeReader(pipe_path)
                writer = PipeWriter(pipe_path)

                self.assertIsInstance(writer, PipeWriter)
                self.assertIsInstance(reader, PipeReader)

                data = b"data"
                self.assertEqual(4, writer.write(data))
                self.assertEqual(data, reader.read(4))

                writer.close()
                reader.close()
                self.assertTrue(os.path.exists(pipe_path))

            self.assertFalse(os.path.exists(pipe_path))
        self.assertFalse(os.path.exists(tmpdir))


if __name__ == "__main__":
    main()
