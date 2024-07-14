# -*- coding: utf-8 -*-

from unittest import TestCase, main

from smipc.cuda.memory import CudaMemory


class MemoryTestCase(TestCase):
    def test_default(self):
        mem1 = CudaMemory(0, 1, 2, 3, 4, [10, 11, 12])
        serialized_data = mem1.to_bytes()
        self.assertIsInstance(serialized_data, bytes)
        self.assertEqual(len(serialized_data), 4 * 9)  # UINT(4byte) * 9 = 36byte

        mem2 = CudaMemory.from_bytes(serialized_data)
        self.assertEqual(mem1, mem2)


if __name__ == "__main__":
    main()
