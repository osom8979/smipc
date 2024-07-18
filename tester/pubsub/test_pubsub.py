# -*- coding: utf-8 -*-

import os
from asyncio import gather, to_thread
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, main

from smipc.pipe.wait import wait_exists
from smipc.pubsub.publisher import Publisher
from smipc.pubsub.subscriber import Subscriber
from smipc.variables import CLIENT_TO_SERVER_SUFFIX, SERVER_TO_CLIENT_SUFFIX


class PubsubTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.p2s_suffix = SERVER_TO_CLIENT_SUFFIX
        self.s2p_suffix = CLIENT_TO_SERVER_SUFFIX
        self.wait_timeout = 4.0

    def create_publisher(self, prefix: str):
        return Publisher(
            prefix,
            p2s_suffix=self.p2s_suffix,
            s2p_suffix=self.s2p_suffix,
        )

    def create_subscriber(self, prefix: str):
        wait_exists(prefix + self.p2s_suffix, self.wait_timeout)
        wait_exists(prefix + self.s2p_suffix, self.wait_timeout)

        return Subscriber(
            prefix,
            p2s_suffix=self.p2s_suffix,
            s2p_suffix=self.s2p_suffix,
        )

    async def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))
            prefix = os.path.join(tmpdir, "test")

            server, client = await gather(
                to_thread(self.create_publisher, prefix),
                to_thread(self.create_subscriber, prefix),
            )
            self.assertIsInstance(server, Publisher)
            self.assertIsInstance(client, Subscriber)

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
