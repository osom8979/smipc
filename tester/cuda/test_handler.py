# -*- coding: utf-8 -*-

from functools import reduce
from unittest import TestCase, main, skipIf

import numpy

from smipc.cuda.compatibility import has_cupy
from smipc.cuda.handler import CudaHandler, cupy_ones


@skipIf(not has_cupy(), "The cupy package is required for the CudaHandler")
class HandlerTestCase(TestCase):
    def test_default(self):
        with self.assertRaises(ValueError):
            CudaHandler((0, 0), dtype=numpy.uint8)

        shape = 1920 * 2, 1080 * 2, 3
        size = reduce(lambda x, y: x * y, shape, 1)

        cpu_ones = numpy.ones(shape, dtype=numpy.uint8)
        self.assertEqual(size, cpu_ones.size)

        gpu_ones = cupy_ones(shape, dtype=numpy.uint8)
        self.assertEqual(size, gpu_ones.size)

        handler = CudaHandler(shape, dtype=numpy.uint8)

        handler.cpu[:] = cpu_ones[:]
        self.assertTrue(numpy.all(handler.cpu == 1))

        handler.copy_async_host_to_device()

        gpu = handler.gpu
        with handler.stream:
            gpu *= 10

        handler.copy_async_device_to_host()
        handler.record()
        handler.synchronize()

        self.assertTrue(numpy.all(handler.cpu == 10))


if __name__ == "__main__":
    main()
