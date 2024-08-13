# -*- coding: utf-8 -*-

from functools import reduce
from unittest import TestCase, main, skipIf

import numpy

from smipc.cuda.alignment import IPC_ALLOCATION_UNIT_SIZE
from smipc.cuda.compatibility import has_cupy
from smipc.cuda.handler import CudaHandler


@skipIf(not has_cupy(), "The cupy package is required for the CudaHandler")
class HandlerTestCase(TestCase):
    def test_default(self):
        with self.assertRaises(ValueError):
            CudaHandler((0, 0), dtype=numpy.uint8)

        shape = 1920, 1080, 3
        size = reduce(lambda x, y: x * y, shape, 1)
        unit = IPC_ALLOCATION_UNIT_SIZE
        unit2x = unit * 2
        unit3x = unit * 3
        self.assertTrue(unit2x < size < unit3x)

        empty = numpy.ones(shape, dtype=numpy.uint8)
        self.assertEqual(size, empty.size)

        handler = CudaHandler(shape, dtype=numpy.uint8)
        self.assertEqual(unit3x, handler.size)

        handler.cpu[:] = empty[:]
        handler.copy_async_host_to_device()
        handler.record()
        handler.synchronize()

        handler.gpu *= 10

        handler.copy_async_device_to_host()
        handler.record()
        handler.synchronize()

        self.assertTrue(numpy.all(handler.cpu.all == 10))


if __name__ == "__main__":
    main()
