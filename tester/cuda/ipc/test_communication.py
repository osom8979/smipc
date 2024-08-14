# -*- coding: utf-8 -*-

from functools import reduce
from multiprocessing import Process, SimpleQueue, set_start_method
from unittest import TestCase, main, skipIf

import numpy

from smipc.cuda.compatibility import has_cupy
from smipc.cuda.ipc.packet import CudaIpcPacket
from smipc.cuda.ipc.provider import CudaIpcProvider
from smipc.cuda.ipc.receiver import CudaIpcReceiver
from smipc.cuda.runtime import cupy_ones


def _receiver_main(queue: SimpleQueue):
    data = queue.get()
    info = CudaIpcPacket.from_bytes(data)

    receiver = CudaIpcReceiver(info, lazy_cpu=False)
    with receiver:
        receiver.wait_event()

        receiver.async_copy_device_to_host()
        receiver.synchronize()

        with receiver.stream:
            gpu = receiver.gpu

            if numpy.all(receiver.cpu == 1):
                gpu += 100
            else:
                gpu += 200

        receiver.record()


@skipIf(not has_cupy(), "The cupy package is required for the CudaHandler")
class CommunicationTestCase(TestCase):
    def test_default(self):
        set_start_method("spawn", force=True)

        shape = 1920 * 2, 1080 * 2, 3
        size = reduce(lambda x, y: x * y, shape, 1)
        dtype = numpy.uint8

        cpu_ones = numpy.ones(shape, dtype=dtype)
        self.assertEqual(size, cpu_ones.size)

        gpu_ones = cupy_ones(shape, dtype=dtype)
        self.assertEqual(size, gpu_ones.size)

        provider = CudaIpcProvider(shape, dtype=dtype)

        queue = SimpleQueue()
        receiver_proc = Process(target=_receiver_main, args=(queue,))
        receiver_proc.start()

        provider.cpu[:] = cpu_ones[:]
        self.assertTrue(numpy.all(provider.cpu == 1))

        provider.async_copy_host_to_device()
        provider.record()
        queue.put(provider.info.to_bytes())

        timeout = 12.0
        receiver_proc.join(timeout=timeout)

        provider.wait_event()
        provider.async_copy_device_to_host()
        provider.synchronize()

        self.assertTrue(numpy.all(provider.cpu == 101))


if __name__ == "__main__":
    main()
