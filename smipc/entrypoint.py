# -*- coding: utf-8 -*-

import os
from sys import exit as sys_exit
from typing import Callable, List, Optional

from smipc.aio.run import has_uvloop
from smipc.apps.client import run_client
from smipc.apps.server import run_server
from smipc.arguments import CMD_CLIENT, CMD_SERVER, CMDS, get_default_arguments
from smipc.cuda.compatibility import has_cupy


def main(
    cmdline: Optional[List[str]] = None,
    printer: Callable[..., None] = print,
) -> int:
    args = get_default_arguments(cmdline)

    if not args.cmd:
        printer("The command does not exist")
        return 1

    assert args.cmd in CMDS
    assert isinstance(args.pipe_dir, str)
    assert isinstance(args.iteration, int)
    assert isinstance(args.data_size, int)
    assert isinstance(args.use_cuda, bool)
    assert isinstance(args.use_uvloop, bool)
    assert isinstance(args.debug, bool)

    pipe_dir = args.pipe_dir
    iteration = args.iteration
    data_size = args.data_size
    use_cuda = args.use_cuda
    use_uvloop = args.use_uvloop
    debug = args.debug

    if not os.path.isdir(pipe_dir):
        printer(f"The pipe directory does not exist: '{pipe_dir}'")
        return 1

    if not os.access(pipe_dir, os.W_OK):
        printer(f"The pipe directory is not writable: '{pipe_dir}'")
        return 1

    if not os.access(pipe_dir, os.R_OK):
        printer(f"The pipe directory is not readable: '{pipe_dir}'")
        return 1

    if iteration <= 0:
        printer("The 'iteration' argument is must be greater than 0")
        return 1

    if data_size <= 0:
        printer("The 'data-size' argument is must be greater than 0")
        return 1

    if use_cuda and not has_cupy():
        printer("The 'cupy' package is not installed")
        return 1

    if use_uvloop and not has_uvloop():
        printer("The 'uvloop' package is not installed")
        return 1

    if debug:
        printer("Enabled debug mode")

    try:
        if args.cmd == CMD_SERVER:
            run_server(pipe_dir, iteration, data_size, use_cuda, use_uvloop, debug)
        elif args.cmd == CMD_CLIENT:
            run_client(pipe_dir, iteration, data_size, use_cuda, use_uvloop, debug)
    except BaseException as e:
        printer(e)
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys_exit(main())
