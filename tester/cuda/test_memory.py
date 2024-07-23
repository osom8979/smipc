# -*- coding: utf-8 -*-

from unittest import TestCase, main

from smipc.cuda.memory import CudaMemory, header_bytes


class MemoryTestCase(TestCase):
    def test_header(self):
        # Header size: UINT(4byte) * 6 = 24bytes
        self.assertEqual(24, header_bytes())

    def test_default(self):
        device_index = 2
        event_handle = b"ABCD"
        memory_handle = b"abcdefg"
        memory_size = 100
        stride = 4
        shape = [10, 11, 12]

        mem1 = CudaMemory(
            device_index,
            event_handle,
            memory_handle,
            memory_size,
            stride,
            shape,
        )

        serialized_data = mem1.to_bytes()
        self.assertIsInstance(serialized_data, bytes)

        mem2 = CudaMemory.from_bytes(serialized_data)
        self.assertEqual(mem1, mem2)

        self.assertEqual(device_index, mem2.device_index)
        self.assertEqual(event_handle, mem2.event_handle)
        self.assertEqual(memory_handle, mem2.memory_handle)
        self.assertEqual(memory_size, mem2.memory_size)
        self.assertEqual(stride, mem2.stride)
        self.assertSequenceEqual(shape, mem2.shape)


if __name__ == "__main__":
    main()
