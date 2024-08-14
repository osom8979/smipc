# -*- coding: utf-8 -*-

from asyncio import run as asyncio_run
from functools import lru_cache
from sys import version_info


@lru_cache
def has_uvloop() -> bool:
    try:
        import uvloop  # noqa
    except ImportError:
        return False
    else:
        return True


def uv_run(coro) -> None:
    from uvloop import install as uvloop_install
    from uvloop import new_event_loop as uvloop_new_event_loop

    if version_info >= (3, 11):
        from asyncio import Runner  # type: ignore[attr-defined]

        with Runner(loop_factory=uvloop_new_event_loop) as runner:
            runner.run(coro)
    else:
        uvloop_install()
        asyncio_run(coro)


def aio_run(coro, use_uvloop=False) -> None:
    if use_uvloop:
        uv_run(coro)
    else:
        asyncio_run(coro)
