# -*- coding: utf-8 -*-

import os
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from smipc.pipe.reader import PipeReader
from smipc.pipe.temp import TemporaryPipe


class ReaderTestCase(TestCase):
    def test_reader_is_not_blocked(self):
        with TemporaryDirectory() as tmpdir:
            with TemporaryPipe(os.path.join(tmpdir, "temp.fifo")) as pipe_path:
                reader = PipeReader(pipe_path)
                self.assertNotEqual(0, reader.fileno())


if __name__ == "__main__":
    main()
