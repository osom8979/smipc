# -*- coding: utf-8 -*-

from functools import reduce
from unittest import TestCase, main, skipIf

import numpy

from smipc.cuda.compatibility import has_cupy
from smipc.cuda.ipc.packet import CudaIpcPacket
from smipc.cuda.ipc.provider import CudaIpcProvider
from smipc.cuda.ipc.receiver import CudaIpcReceiver
from smipc.cuda.runtime import cupy_ones


@skipIf(not has_cupy(), "The cupy package is required for the CudaHandler")
class ReceiverTestCase(TestCase):
    def test_default(self):
        shape = 1920 * 2, 1080 * 2, 3
        size = reduce(lambda x, y: x * y, shape, 1)

        cpu_ones = numpy.ones(shape, dtype=numpy.uint8)
        self.assertEqual(size, cpu_ones.size)

        gpu_ones = cupy_ones(shape, dtype=numpy.uint8)
        self.assertEqual(size, gpu_ones.size)

        provider = CudaIpcProvider(shape, dtype=numpy.uint8)
        info = CudaIpcPacket.from_bytes(provider.info.to_bytes())
        receiver = CudaIpcReceiver(info, lazy_cpu=False)
        self.assertEqual(receiver.info, provider.info)

        provider.cpu[:] = cpu_ones[:]
        self.assertTrue(numpy.all(provider.cpu == 1))

        provider.async_copy_host_to_device()

        gpu = provider.gpu
        with provider.stream:
            gpu *= 10

        provider.record()
        receiver.wait_event()

        receiver.async_copy_device_to_host()
        receiver.record()
        receiver.synchronize()
        self.assertTrue(numpy.all(receiver.cpu == 10))


if __name__ == "__main__":
    main()
