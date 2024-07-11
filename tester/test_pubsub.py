# -*- coding: utf-8 -*-

import os
from asyncio import gather, to_thread
from tempfile import TemporaryDirectory
from time import sleep, time
from typing import Optional
from unittest import IsolatedAsyncioTestCase, main

from smipc.publisher import SmipcPublisher
from smipc.subscriber import SmipcSubscriber
from smipc.variables import PUB2SUB_SUFFIX, SUB2PUB_SUFFIX


def wait_for_file(path: str, timeout: Optional[float] = None, step=0.001) -> None:
    begin = time()
    while not os.path.exists(path):
        if timeout is not None and (time() - begin) > timeout:
            raise TimeoutError
        sleep(step)


class PubsubTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.p2s_suffix = PUB2SUB_SUFFIX
        self.s2p_suffix = SUB2PUB_SUFFIX
        self.wait_timeout = 4.0

    def create_publisher(self, prefix: str):
        return SmipcPublisher(
            prefix,
            p2s_suffix=self.p2s_suffix,
            s2p_suffix=self.s2p_suffix,
        )

    def create_subscriber(self, prefix: str):
        wait_for_file(prefix + self.p2s_suffix, self.wait_timeout)
        wait_for_file(prefix + self.s2p_suffix, self.wait_timeout)
        return SmipcSubscriber(
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
