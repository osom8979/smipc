# -*- coding: utf-8 -*-

import os
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from smipc.protocols.header import Opcode
from smipc.server.base import BaseServer


class BaseTestCase(TestCase):
    def test_default(self):
        with TemporaryDirectory() as tmpdir:
            self.assertTrue(os.path.isdir(tmpdir))
            self.server = BaseServer(tmpdir)

            key1 = "1"
            channel1 = self.server.open(key1)
            client1 = channel1.create_client_proto()
            self.assertEqual(1, len(self.server))

            key2 = "2"
            channel2 = self.server.open(key2)
            client2 = channel2.create_client_proto()
            self.assertEqual(2, len(self.server))

            data1 = b"RGB" * 3840 * 2160  # 4K RGB Image
            self.assertEqual(len(data1), channel1.send(data1).sm_byte)
            self.assertEqual(data1, client1.recv())
            self.assertEqual(Opcode.SM_RESTORE, channel1.recv_with_header()[0].opcode)
            self.assertEqual(len(data1), client1.send(data1).sm_byte)
            self.assertEqual(data1, channel1.recv())
            self.assertEqual(Opcode.SM_RESTORE, client1.recv_with_header()[0].opcode)
            channel1.close()
            client1.close()
            channel1.cleanup()

            data2 = b"123" * 3840 * 2160  # 4K RGB Image
            self.assertEqual(len(data2), channel2.send(data2).sm_byte)
            self.assertEqual(data2, client2.recv())
            self.assertEqual(Opcode.SM_RESTORE, channel2.recv_with_header()[0].opcode)
            self.assertEqual(len(data2), client2.send(data2).sm_byte)
            self.assertEqual(data2, channel2.recv())
            self.assertEqual(Opcode.SM_RESTORE, client2.recv_with_header()[0].opcode)
            channel2.close()
            client2.close()
            channel2.cleanup()


if __name__ == "__main__":
    main()
