# -*- coding: utf-8 -*-

from functools import lru_cache


@lru_cache
def has_cupy() -> bool:
    try:
        import cupy  # noqa
    except ImportError:
        return False
    else:
        return True
