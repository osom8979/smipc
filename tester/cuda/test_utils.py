# -*- coding: utf-8 -*-

from unittest import TestCase, main, skipIf

from smipc.cuda.utils import (
    IPC_ALLOCATION_UNIT_SIZE,
    align_ipc_malloc_size,
    compatible_ipc,
    has_cupy,
)


class UtilsTestCase(TestCase):
    def test_align_ipc_malloc_size(self):
        self.assertEqual(IPC_ALLOCATION_UNIT_SIZE, align_ipc_malloc_size(1))

    @skipIf(not has_cupy(), "The cupy package is required for the CudaHandler")
    def test_compatible_ipc(self):
        self.assertTrue(compatible_ipc())


if __name__ == "__main__":
    main()
