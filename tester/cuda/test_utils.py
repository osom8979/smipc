# -*- coding: utf-8 -*-

from unittest import TestCase, main, skipIf

from smipc.cuda.utils import compatible_ipc, has_cupy


class UtilsTestCase(TestCase):
    @skipIf(not has_cupy(), "The cupy package is required for the CudaHandler")
    def test_compatible_ipc(self):
        self.assertTrue(compatible_ipc())


if __name__ == "__main__":
    main()
