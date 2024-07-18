# -*- coding: utf-8 -*-

import os
from asyncio import Event
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple
from unittest import IsolatedAsyncioTestCase, main
from weakref import ReferenceType

from smipc.decorators.override import override
from smipc.pipe.temp_pair import TemporaryPipePair
from smipc.protocols.sm import SmProtocol
from smipc.server.aio import AioChannel, AioServer


class _TestAioChannel(AioChannel):
    buffer: List[bytes]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer = list()
        self.event = Event()

    @override
    async def on_recv(self, data: bytes) -> None:
        self.buffer.append(data)
        self.event.set()


class _TestAioServer(AioServer):
    buffer: List[Tuple[AioChannel, bytes]]

    def __init__(self, root: str):
        super().__init__(root)
        self.buffer = list()
        self.event = Event()

    @override
    def on_create_channel(
        self,
        key: str,
        proto: SmProtocol,
        weak_base: Optional[ReferenceType],
        fifos: Optional[TemporaryPipePair],
    ):
        return _TestAioChannel(key, proto, weak_base, fifos)

    @override
    async def on_recv(self, channel: AioChannel, data: bytes) -> None:
        self.buffer.append((channel, data))
        channel.send(data)
        self.event.set()


class AioTestCase(IsolatedAsyncioTestCase):
    async def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))
            self.server = _TestAioServer(tmpdir)

            key1 = "1"
            self.server.open(key1)
            client1 = self.server.create_client_channel(key1)
            self.assertIsInstance(client1, _TestAioChannel)
            self.assertEqual(1, len(self.server))
            self.assertEqual(0, len(self.server.buffer))

            with self.assertRaises(RuntimeError):
                self.server.recv(key1)
            with self.assertRaises(RuntimeError):
                self.server.recv_with_header(key1)

            with self.assertRaises(RuntimeError):
                client1.recv()
            with self.assertRaises(RuntimeError):
                client1.recv_with_header()

            data1 = b"RGB" * 3840 * 2160  # 4K RGB Image
            self.assertEqual(len(data1), client1.send(data1).sm_byte)

            await self.server.event.wait()
            self.assertEqual(1, len(self.server.buffer))

            buf = self.server.buffer.pop()
            self.assertEqual(key1, buf[0].key)
            self.assertEqual(data1, buf[1])

            await client1.event.wait()
            self.assertEqual(1, len(client1.buffer))
            client_buf = client1.buffer.pop()
            self.assertEqual(data1, client_buf)

            client1.close()
            self.server.close(key1)
            self.server.cleanup(key1)


if __name__ == "__main__":
    main()
