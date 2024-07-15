# -*- coding: utf-8 -*-

import os
from asyncio import gather, to_thread
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, main

from smipc.pipe.temp import TemporaryPipe
from smipc.protocols.sm import SmProtocol


class CpuTestCase(IsolatedAsyncioTestCase):
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
                to_thread(lambda: SmProtocol.from_fifo(s2c_path, c2s_path)),
                to_thread(lambda: SmProtocol.from_fifo(c2s_path, s2c_path)),
            )
            self.assertIsInstance(server, SmProtocol)
            self.assertIsInstance(client, SmProtocol)

            data = b"RGB" * 3840 * 2160  # 4K RGB Image
            self.assertEqual(3840 * 2160 * 3, len(data))

            send_info1 = server.send(data)

            send_pipe_size1 = server.header_size + len(send_info1.sm_name)
            self.assertEqual(send_pipe_size1, send_info1.pipe_byte)
            self.assertEqual(len(data), send_info1.sm_byte)
            self.assertEqual(data, client.recv())
            self.assertIsNone(server.recv())  # Opcode.SM_RESTORE

            send_info2 = client.send(data)
            send_pipe_size2 = client.header_size + len(send_info2.sm_name)
            self.assertEqual(send_pipe_size2, send_info2.pipe_byte)
            self.assertEqual(len(data), send_info2.sm_byte)
            self.assertEqual(data, server.recv())
            self.assertIsNone(client.recv())  # Opcode.SM_RESTORE

            server.close()
            client.close()

            s2c_pipe.cleanup()
            c2s_pipe.cleanup()
            self.assertFalse(os.path.exists(s2c_path))
            self.assertFalse(os.path.exists(c2s_path))


if __name__ == "__main__":
    main()
