# -*- coding: utf-8 -*-

import os
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from functools import lru_cache
from typing import Final, List, Optional, Sequence

PROG: Final[str] = "smipc"
DESCRIPTION: Final[str] = "Shared Memory IPC"

CMD_SERVER: Final[str] = "server"
CMD_SERVER_HELP: Final[str] = "Benchmark server"
CMD_SERVER_EPILOG = f"""
Simply usage:
  {PROG} {CMD_SERVER}
"""

CMD_CLIENT: Final[str] = "client"
CMD_CLIENT_HELP: Final[str] = "Benchmark client"
CMD_CLIENT_EPILOG = f"""
Simply usage:
  {PROG} {CMD_CLIENT}
"""

CMDS: Final[Sequence[str]] = CMD_SERVER, CMD_CLIENT

DEFAULT_CHANNEL: Final[str] = "0"
LOCAL_ROOT_DIR: Final[str] = "pipe"
DEFAULT_ITERATION: Final[int] = 1_000
DEFAULT_FRAME_WIDTH: Final[int] = 1920
DEFAULT_FRAME_HEIGHT: Final[int] = 1080
DEFAULT_FRAME_CHANNELS: Final[int] = 3
DEFAULT_DATA_SIZE = DEFAULT_FRAME_WIDTH * DEFAULT_FRAME_HEIGHT * DEFAULT_FRAME_CHANNELS


@lru_cache
def version() -> str:
    # [IMPORTANT] Avoid 'circular import' issues
    from smipc import __version__

    return __version__


def add_server_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(
        name=CMD_SERVER,
        help=CMD_SERVER_HELP,
        formatter_class=RawDescriptionHelpFormatter,
        epilog=CMD_SERVER_EPILOG,
    )
    assert isinstance(parser, ArgumentParser)


def add_client_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(
        name=CMD_CLIENT,
        help=CMD_CLIENT_HELP,
        formatter_class=RawDescriptionHelpFormatter,
        epilog=CMD_CLIENT_EPILOG,
    )
    assert isinstance(parser, ArgumentParser)
    parser.add_argument(
        "--frame-width",
        metavar="int",
        default=DEFAULT_FRAME_WIDTH,
        help=f"Frame width (default: {DEFAULT_FRAME_WIDTH})",
    )
    parser.add_argument(
        "--frame-height",
        metavar="int",
        default=DEFAULT_FRAME_HEIGHT,
        help=f"Frame width (default: {DEFAULT_FRAME_HEIGHT})",
    )
    parser.add_argument(
        "--frame-channels",
        metavar="int",
        default=DEFAULT_FRAME_CHANNELS,
        help=f"Frame width (default: {DEFAULT_FRAME_CHANNELS})",
    )


def default_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog=PROG,
        description=DESCRIPTION,
        formatter_class=RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--root-dir",
        metavar="dir",
        default=os.path.join(os.getcwd(), LOCAL_ROOT_DIR),
        help="The directory location where the pipe file will be created",
    )
    parser.add_argument(
        "--channel",
        default=DEFAULT_CHANNEL,
        help="Channel name",
    )
    parser.add_argument(
        "--iteration",
        "-i",
        metavar="int",
        default=DEFAULT_ITERATION,
        help=f"Number of test repetitions (default: {DEFAULT_ITERATION})",
    )

    parser.add_argument(
        "--use-cuda",
        action="store_true",
        default=False,
        help="Apply tests using CUDA IPC",
    )
    parser.add_argument(
        "--use-uvloop",
        action="store_true",
        default=False,
        help="Replace the event loop with uvloop",
    )

    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
        help="Enable debugging mode",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Be more verbose/talkative during the operation",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=version(),
    )

    subparsers = parser.add_subparsers(dest="cmd")
    add_server_parser(subparsers)
    add_client_parser(subparsers)
    return parser


def get_default_arguments(
    cmdline: Optional[List[str]] = None,
    namespace: Optional[Namespace] = None,
) -> Namespace:
    parser = default_argument_parser()
    return parser.parse_known_args(cmdline, namespace)[0]
