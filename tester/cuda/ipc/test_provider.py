# -*- coding: utf-8 -*-

from functools import reduce
from unittest import TestCase, main, skipIf

import numpy

from smipc.cuda.compatibility import has_cupy
from smipc.cuda.ipc.provider import CudaIpcProvider
from smipc.cuda.runtime import cupy_ones


@skipIf(not has_cupy(), "The cupy package is required for the CudaHandler")
class ProviderTestCase(TestCase):
    def test_shape_error(self):
        with self.assertRaises(ValueError):
            CudaIpcProvider((0, 0), dtype=numpy.uint8)

    def test_default(self):
        shape = 1920 * 2, 1080 * 2, 3
        size = reduce(lambda x, y: x * y, shape, 1)

        cpu_ones = numpy.ones(shape, dtype=numpy.uint8)
        self.assertEqual(size, cpu_ones.size)

        gpu_ones = cupy_ones(shape, dtype=numpy.uint8)
        self.assertEqual(size, gpu_ones.size)

        handler = CudaIpcProvider(shape, dtype=numpy.uint8)

        handler.cpu[:] = cpu_ones[:]
        self.assertTrue(numpy.all(handler.cpu == 1))

        handler.async_copy_host_to_device()

        gpu = handler.gpu
        with handler.stream:
            gpu *= 10

        handler.async_copy_device_to_host()
        handler.record()
        handler.synchronize()

        self.assertTrue(numpy.all(handler.cpu == 10))


if __name__ == "__main__":
    main()
