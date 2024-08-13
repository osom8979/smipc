# -*- coding: utf-8 -*-

from unittest import TestCase, main

from smipc.cuda.alignment import IPC_ALLOCATION_UNIT_SIZE, align_ipc_malloc_size


class AlignmentTestCase(TestCase):
    def test_align_ipc_malloc_size(self):
        with self.assertRaises(ValueError):
            align_ipc_malloc_size(-1)
        with self.assertRaises(ValueError):
            align_ipc_malloc_size(0)

        self.assertEqual(
            IPC_ALLOCATION_UNIT_SIZE,
            align_ipc_malloc_size(1),
        )
        self.assertEqual(
            IPC_ALLOCATION_UNIT_SIZE,
            align_ipc_malloc_size(IPC_ALLOCATION_UNIT_SIZE),
        )
        self.assertEqual(
            IPC_ALLOCATION_UNIT_SIZE * 2,
            align_ipc_malloc_size(IPC_ALLOCATION_UNIT_SIZE + 1),
        )


if __name__ == "__main__":
    main()
