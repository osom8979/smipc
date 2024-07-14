# -*- coding: utf-8 -*-

from unittest import TestCase, main

from smipc.cuda.handler import CudaHandler


class HandlerTestCase(TestCase):
    def test_default(self):
        handler = CudaHandler()
        self.assertIsNone(handler.memory)


if __name__ == "__main__":
    main()
