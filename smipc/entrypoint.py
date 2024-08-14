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
    assert isinstance(args.root_dir, str)
    assert isinstance(args.channel, str)
    assert isinstance(args.use_cuda, bool)
    assert isinstance(args.use_uvloop, bool)

    root_dir = args.root_dir
    channel = args.channel
    use_cuda = args.use_cuda
    use_uvloop = args.use_uvloop

    if not os.path.isdir(root_dir):
        printer(f"The pipe directory does not exist: '{root_dir}'")
        return 1

    if not os.access(root_dir, os.W_OK):
        printer(f"The pipe directory is not writable: '{root_dir}'")
        return 1

    if not os.access(root_dir, os.R_OK):
        printer(f"The pipe directory is not readable: '{root_dir}'")
        return 1

    if not channel:
        printer("The 'channel' argument is required")
        return 1

    if use_cuda and not has_cupy():
        printer("The 'cupy' package is not installed")
        return 1

    if use_uvloop and not has_uvloop():
        printer("The 'uvloop' package is not installed")
        return 1

    iteration = 0
    data_size = 0

    if args.cmd == CMD_CLIENT:
        assert isinstance(args.iteration, int)
        assert isinstance(args.data_size, int)

        iteration = args.iteration
        data_size = args.data_size

        if iteration <= 0:
            printer("The 'iteration' argument is must be greater than 0")
            return 1

        if data_size <= 0:
            printer("The 'data-size' argument is must be greater than 0")
            return 1

    try:
        if args.cmd == CMD_SERVER:
            run_server(
                root_dir=root_dir,
                channel=channel,
                use_cuda=use_cuda,
                use_uvloop=use_uvloop,
                printer=printer,
            )
        elif args.cmd == CMD_CLIENT:
            run_client(
                root_dir=root_dir,
                channel=channel,
                iteration=iteration,
                data_size=data_size,
                use_cuda=use_cuda,
                use_uvloop=use_uvloop,
                printer=printer,
            )
    except BaseException as e:
        printer(e)
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys_exit(main())
