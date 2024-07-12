# -*- coding: utf-8 -*-

import os
from gc import collect
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from smipc.pipe.temp import TemporaryPipe


class TempTestCase(TestCase):
    def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))

            file_path = os.path.join(tmpdir, "temp.fifo")
            self.assertFalse(os.path.exists(file_path))

            pipe = TemporaryPipe(file_path)

            with pipe as pipe_path:
                self.assertEqual(pipe_path, file_path)
                self.assertTrue(os.path.exists(pipe_path))
                self.assertTrue(os.path.exists(file_path))

            self.assertFalse(os.path.exists(file_path))

        self.assertFalse(os.path.isdir(tmpdir))
        self.assertFalse(os.path.exists(tmpdir))

    def test_finalizer(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))

            file_path = os.path.join(tmpdir, "temp.fifo")
            self.assertFalse(os.path.exists(file_path))

            pipe = TemporaryPipe(file_path)
            finalizer = pipe._finalizer

            self.assertTrue(os.path.exists(file_path))
            self.assertTrue(finalizer.alive)

            # -------
            del pipe
            collect()
            # -------

            self.assertFalse(finalizer.alive)
            self.assertFalse(os.path.exists(file_path))

        self.assertFalse(os.path.isdir(tmpdir))
        self.assertFalse(os.path.exists(tmpdir))


if __name__ == "__main__":
    main()
