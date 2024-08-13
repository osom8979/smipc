# -*- coding: utf-8 -*-

from unittest import TestCase, main, skipIf

from smipc.cuda.alignment import IPC_ALLOCATION_UNIT_SIZE
from smipc.cuda.compatibility import has_cupy
from smipc.cuda.handler import CudaHandler


@skipIf(not has_cupy(), "The cupy package is required for the CudaHandler")
class HandlerTestCase(TestCase):
    def test_default(self):
        with self.assertRaises(ValueError):
            CudaHandler(0)

        handler = CudaHandler(1)
        self.assertEqual(IPC_ALLOCATION_UNIT_SIZE, handler.size)


if __name__ == "__main__":
    main()
