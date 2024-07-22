# -*- coding: utf-8 -*-

from gc import collect
from unittest import TestCase, main, skipIf

from smipc.cuda.utils import ALLOCATION_UNIT_SIZE, has_cupy, has_numpy


@skipIf(
    not has_cupy() or not has_numpy(),
    "The 'cupy' and 'numpy' package is required for the CudaHandler",
)
class CupyTestCase(TestCase):
    def setUp(self):
        # noinspection PyUnresolvedReferences
        import cupy as _cp
        import numpy as _np

        self.cp = _cp
        self.np = _np

    def test_pinned_memory_pool(self):
        cpu_pool = self.cp.get_default_pinned_memory_pool()
        self.assertEqual(0, cpu_pool.n_free_blocks())

        size1_alloc = ALLOCATION_UNIT_SIZE
        size1 = 4
        mem1 = cpu_pool.malloc(size1_alloc)
        self.assertEqual(0, cpu_pool.n_free_blocks())

        arr1 = self.np.frombuffer(mem1, self.np.int8, size1).reshape((size1,))
        self.assertEqual(0, cpu_pool.n_free_blocks())
        self.assertEqual([0, 0, 0, 0], arr1.tolist())

        arr1[:] = 1
        self.assertEqual([1, 1, 1, 1], arr1.tolist())

        del arr1
        collect()
        self.assertEqual(0, cpu_pool.n_free_blocks())

        arr2 = self.np.frombuffer(mem1, self.np.int8, size1).reshape((size1,))
        self.assertEqual(0, cpu_pool.n_free_blocks())
        self.assertEqual([1, 1, 1, 1], arr2.tolist())

        del arr2
        collect()
        self.assertEqual(0, cpu_pool.n_free_blocks())

        # ----
        del mem1  # == mem1.mem.free()
        collect()
        self.assertEqual(1, cpu_pool.n_free_blocks())
        # ----

        size2_alloc = ALLOCATION_UNIT_SIZE + 1
        size2 = 8
        mem2 = cpu_pool.malloc(size2_alloc)
        self.assertEqual(1, cpu_pool.n_free_blocks())

        arr3 = self.np.frombuffer(mem2, self.np.int8, size2).reshape((size2,))
        self.assertEqual(1, cpu_pool.n_free_blocks())
        self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0], arr3.tolist())

        arr3[:] = 2
        self.assertEqual([2, 2, 2, 2, 2, 2, 2, 2], arr3.tolist())

        del arr3
        collect()
        self.assertEqual(1, cpu_pool.n_free_blocks())

        arr4 = self.np.frombuffer(mem2, self.np.int8, size2).reshape((size2,))
        self.assertEqual(1, cpu_pool.n_free_blocks())
        self.assertEqual([2, 2, 2, 2, 2, 2, 2, 2], arr4.tolist())

        del arr4
        collect()
        self.assertEqual(1, cpu_pool.n_free_blocks())

        # ----
        del mem2  # == mem2.mem.free()
        collect()
        self.assertEqual(2, cpu_pool.n_free_blocks())
        # ----

        cpu_pool.free_all_blocks()
        self.assertEqual(0, cpu_pool.n_free_blocks())

    def test_pool(self):
        # https://docs.cupy.dev/en/stable/user_guide/memory.html#memory-pool-operations
        gpu_pool = self.cp.get_default_memory_pool()
        cpu_pool = self.cp.get_default_pinned_memory_pool()

        self.assertEqual(0, gpu_pool.used_bytes())
        self.assertEqual(0, gpu_pool.total_bytes())
        self.assertEqual(0, cpu_pool.n_free_blocks())

        # Create an array on CPU.
        # NumPy allocates 400 bytes in CPU (not managed by CuPy memory pool)
        a_cpu = self.np.ndarray(100, dtype=self.np.float32)
        self.assertEqual(400, a_cpu.nbytes)

        self.assertEqual(0, gpu_pool.used_bytes())
        self.assertEqual(0, gpu_pool.total_bytes())
        self.assertEqual(0, cpu_pool.n_free_blocks())

        # Transfer the array from CPU to GPU.
        # This allocates 400 bytes from the device memory pool, and another 400
        # bytes from the pinned memory pool. The allocated pinned memory will be
        # released just after the transfer is complete. Note that the actual
        # allocation size may be rounded to larger value than the requested size
        # for performance.
        a = self.cp.array(a_cpu)
        self.assertEqual(400, a.nbytes)
        self.assertEqual(512, gpu_pool.used_bytes())
        self.assertEqual(512, gpu_pool.total_bytes())
        self.assertEqual(1, cpu_pool.n_free_blocks())

        # When the array goes out of scope, the allocated device memory is released
        # and kept in the pool for future reuse.
        del a
        self.assertEqual(0, gpu_pool.used_bytes())
        self.assertEqual(512, gpu_pool.total_bytes())
        self.assertEqual(1, cpu_pool.n_free_blocks())

        gpu_pool.free_all_blocks()
        cpu_pool.free_all_blocks()
        self.assertEqual(0, gpu_pool.used_bytes())
        self.assertEqual(0, gpu_pool.total_bytes())
        self.assertEqual(0, cpu_pool.n_free_blocks())

    def test_stream(self):
        # a_cpu = self.np.ones((10000, 10000), dtype=self.np.float32)
        # b_cpu = self.np.ones((10000, 10000), dtype=self.np.float32)

        # # np.ndarray with pinned memory
        # a_cpu = pinned_array(a_cpu)
        # b_cpu = pinned_array(b_cpu)

        # a_stream = cp.cuda.Stream(non_blocking=True)
        # b_stream = cp.cuda.Stream(non_blocking=True)

        # a_gpu = cp.empty_like(a_cpu)
        # b_gpu = cp.empty_like(b_cpu)

        # a_gpu.set(a_cpu, stream=a_stream)
        # b_gpu.set(b_cpu, stream=b_stream)

        # # wait until a_cpu is copied in a_gpu
        # a_stream.synchronize()
        # # This line runs parallel to b_gpu.set()
        # a_gpu *= 2
        pass


if __name__ == "__main__":
    main()
