# -*- coding: utf-8 -*-

from typing import Final

# https://github.com/pytorch/pytorch/blob/main/aten/src/ATen/cuda/detail/OffsetCalculator.cuh
# If element_sizes is nullptr, then the strides will be in bytes, otherwise
# the strides will be in # of elements.
# Operands that share the same shape, but may have different strides.
# OffsetCalculator iterates the tensor in a column-major order
TORCH_MAX_DIMS_ROCM: Final[int] = 16
TORCH_MAX_DIMS_DEFAULT: Final[int] = 25

# https://numpy.org/doc/stable/reference/c-api/array.html#c.NPY_MAXDIMS
# The maximum number of dimensions that may be used by NumPy.
# This is set to 64 and was 32 before NumPy 2.
NPY1_MAX_DIMS: Final[int] = 32
NPY2_MAX_DIMS: Final[int] = 64
