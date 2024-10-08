# -*- coding: utf-8 -*-

import os
from asyncio import gather, to_thread
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, main

from smipc.pipe.duplex import FullDuplexPipe
from smipc.pipe.temp import TemporaryPipe


class DuplexTestCase(IsolatedAsyncioTestCase):
    async def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))

            s2c_path = os.path.join(tmpdir, "s2c.fifo")
            c2s_path = os.path.join(tmpdir, "c2s.fifo")
            self.assertFalse(os.path.exists(s2c_path))
            self.assertFalse(os.path.exists(c2s_path))

            s2c_pipe = TemporaryPipe(s2c_path)
            c2s_pipe = TemporaryPipe(c2s_path)
            self.assertTrue(os.path.exists(s2c_path))
            self.assertTrue(os.path.exists(c2s_path))

            server, client = await gather(
                to_thread(lambda: FullDuplexPipe.from_fifo(s2c_path, c2s_path)),
                to_thread(lambda: FullDuplexPipe.from_fifo(c2s_path, s2c_path)),
            )
            self.assertIsInstance(server, FullDuplexPipe)
            self.assertIsInstance(client, FullDuplexPipe)

            s2c_data = b"data"
            self.assertEqual(4, server.write(s2c_data))
            self.assertEqual(s2c_data, client.read(4))

            c2s_data = b"data"
            self.assertEqual(4, client.write(c2s_data))
            self.assertEqual(c2s_data, server.read(4))

            server.close()
            client.close()

            s2c_pipe.cleanup()
            c2s_pipe.cleanup()
            self.assertFalse(os.path.exists(s2c_path))
            self.assertFalse(os.path.exists(c2s_path))

            with self.assertRaises(OSError):
                server.close()
            with self.assertRaises(OSError):
                client.close()


if __name__ == "__main__":
    main()
