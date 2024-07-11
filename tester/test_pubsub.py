# -*- coding: utf-8 -*-

import os
from asyncio import gather, to_thread
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, main

from smipc.publisher import SmipcPublisher
from smipc.subscriber import SmipcSubscriber


class PubsubTestCase(IsolatedAsyncioTestCase):
    async def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))
            prefix = os.path.join(tmpdir, "test")

            server, client = await gather(
                to_thread(lambda: SmipcPublisher(prefix)),
                to_thread(lambda: SmipcSubscriber(prefix)),
            )
            self.assertIsInstance(server, SmipcPublisher)
            self.assertIsInstance(client, SmipcSubscriber)

            data = b"RGB" * 3840 * 2160  # 4K RGB Image
            self.assertEqual(3840 * 2160 * 3, len(data))

            self.assertEqual(len(data), server.send(data).sm_byte)
            self.assertEqual(data, client.recv())
            self.assertIsNone(server.recv())  # Opcode.SM_RESTORE

            self.assertEqual(len(data), client.send(data).sm_byte)
            self.assertEqual(data, server.recv())
            self.assertIsNone(client.recv())  # Opcode.SM_RESTORE

            server.close()
            client.close()


if __name__ == "__main__":
    main()
