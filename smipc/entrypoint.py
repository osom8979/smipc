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
    assert isinstance(args.iteration, int)
    assert isinstance(args.use_cuda, bool)
    assert isinstance(args.use_uvloop, bool)
    assert isinstance(args.debug, bool)
    assert isinstance(args.verbose, int)

    root_dir = args.root_dir
    channel = args.channel
    iteration = args.iteration
    use_cuda = args.use_cuda
    use_uvloop = args.use_uvloop
    debug = args.debug
    verbose = args.verbose

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

    if iteration <= 0:
        printer("The 'iteration' argument is must be greater than 0")
        return 1

    frame_width = 0
    frame_height = 0
    frame_channels = 0

    if args.cmd == CMD_CLIENT:
        assert isinstance(args.frame_width, int)
        assert isinstance(args.frame_height, int)
        assert isinstance(args.frame_channels, int)

        frame_width = args.frame_width
        frame_height = args.frame_height
        frame_channels = args.frame_channels

        if frame_width <= 0:
            printer("The 'frame_width' argument is must be greater than 0")
            return 1

        if frame_height <= 0:
            printer("The 'frame_height' argument is must be greater than 0")
            return 1

        if frame_channels <= 0:
            printer("The 'frame_channels' argument is must be greater than 0")
            return 1

    try:
        if args.cmd == CMD_SERVER:
            run_server(
                root=root_dir,
                key=channel,
                iteration=iteration,
                use_cuda=use_cuda,
                debug=debug,
                verbose=verbose,
                printer=printer,
            )
        elif args.cmd == CMD_CLIENT:
            run_client(
                root=root_dir,
                key=channel,
                iteration=iteration,
                frame_width=frame_width,
                frame_height=frame_height,
                frame_channels=frame_channels,
                use_cuda=use_cuda,
                debug=debug,
                verbose=verbose,
                printer=printer,
            )
    except BaseException as e:
        printer(e)
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys_exit(main())
