# -*- coding: utf-8 -*-

import os
from asyncio import Queue
from tempfile import TemporaryDirectory
from time import time
from typing import Optional
from unittest import IsolatedAsyncioTestCase, main
from weakref import ReferenceType

from smipc.decorators.override import override
from smipc.pipe.temp_pair import TemporaryPipePair
from smipc.protocols.sm import SmProtocol
from smipc.server.aio import AioChannel, AioServer


class _TestAioChannel(AioChannel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer = Queue[bytes]()

    @override
    async def on_recv(self, data: bytes) -> None:
        await self.buffer.put(data)


class _TestAioServer(AioServer):
    def __init__(self, root: str):
        super().__init__(root)
        self.buffer = Queue[bytes]()

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
        await self.buffer.put(data)
        channel.send(data)


class AioTestCase(IsolatedAsyncioTestCase):
    async def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))
            server = _TestAioServer(tmpdir)

            key1 = "1"
            server.open(key1)
            client1 = server.create_client_channel(key1)
            self.assertIsInstance(client1, _TestAioChannel)
            self.assertEqual(1, len(server))

            with self.assertRaises(RuntimeError):
                server.recv(key1)
            with self.assertRaises(RuntimeError):
                server.recv_with_header(key1)

            with self.assertRaises(RuntimeError):
                client1.recv()
            with self.assertRaises(RuntimeError):
                client1.recv_with_header()

            data1 = b"RGB" * 3840 * 2160  # 4K RGB Image
            # data1 = b"RGB" * 1920 * 1080  # FHD

            self.assertEqual(len(data1), client1.send(data1).sm_byte)
            server_buf1 = await server.buffer.get()
            self.assertEqual(data1, server_buf1)
            client_buf1 = await client1.buffer.get()
            self.assertEqual(data1, client_buf1)

            count = 10
            total_duration = 0.0

            for _ in range(count):
                begin = time()
                self.assertEqual(len(data1), client1.send(data1).sm_byte)

                server_buf1 = await server.buffer.get()
                self.assertEqual(data1, server_buf1)

                client_buf1 = await client1.buffer.get()
                self.assertEqual(data1, client_buf1)

                duration = time() - begin
                total_duration += duration

            mean_duration = total_duration / count
            print(f"\nMean duration: {mean_duration:.3f}s (count={count})")

            client1.close()
            server.close(key1)
            server.cleanup(key1)


if __name__ == "__main__":
    main()
