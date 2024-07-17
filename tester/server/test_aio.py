# -*- coding: utf-8 -*-

import os
from asyncio import Event
from tempfile import TemporaryDirectory
from typing import List, Tuple
from unittest import IsolatedAsyncioTestCase, main

from smipc.decorators.override import override
from smipc.protocols.header import Opcode
from smipc.server.aio import AioServer
from smipc.server.base import Channel


class _TestAioServer(AioServer):
    buffer: List[Tuple[Channel, bytes]]

    def __init__(self, root: str):
        super().__init__(root)
        self.buffer = list()
        self.event = Event()

    @override
    async def on_recv(self, channel: Channel, data: bytes) -> None:
        self.buffer.append((channel, data))
        channel.send(data)
        self.event.set()


class AioTestCase(IsolatedAsyncioTestCase):
    async def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))
            self.server = _TestAioServer(tmpdir)

            key1 = "1"
            channel1 = self.server.open(key1)
            client1 = channel1.create_client_proto()
            self.assertEqual(1, len(self.server))
            self.assertEqual(0, len(self.server.buffer))

            data1 = b"RGB" * 3840 * 2160  # 4K RGB Image
            self.assertEqual(len(data1), client1.send(data1).sm_byte)
            await self.server.event.wait()
            self.assertEqual(1, len(self.server.buffer))
            buf = self.server.buffer.pop()
            self.assertEqual(key1, buf[0].key)
            self.assertEqual(data1, buf[1])

            self.assertEqual(Opcode.SM_RESTORE, client1.recv_with_header()[0].opcode)
            self.assertEqual(data1, client1.recv())

            client1.close()
            self.server.close(key1)
            self.server.cleanup(key1)


if __name__ == "__main__":
    main()
