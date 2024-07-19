# -*- coding: utf-8 -*-

from unittest import TestCase, main, skipIf

from smipc.cuda.handler import CudaHandler
from smipc.cuda.utils import has_cupy


@skipIf(not has_cupy(), "The cupy package is required for the CudaHandler")
class HandlerTestCase(TestCase):
    def test_default(self):
        handler = CudaHandler()
        self.assertIsNone(handler.memory)


if __name__ == "__main__":
    main()
