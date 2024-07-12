# -*- coding: utf-8 -*-

from unittest import TestCase, main

from smipc.protocols.header import Header, Opcode


class HeaderTestCase(TestCase):
    def test_default(self):
        header = Header()
        serialized_data = header.encode(Opcode.PIPE_DIRECT, 11, 99)
        self.assertIsInstance(serialized_data, bytes)
        self.assertEqual(len(serialized_data), header.size)


if __name__ == "__main__":
    main()
