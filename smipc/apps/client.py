# -*- coding: utf-8 -*-

import os
from typing import Optional

from smipc.arguments import DEFAULT_DATA_SIZE, DEFAULT_ITERATION, LOCAL_PIPE_DIR


def run_client(
    pipe_dir: Optional[str] = None,
    iteration=DEFAULT_ITERATION,
    data_size=DEFAULT_DATA_SIZE,
    use_cuda=False,
    use_uvloop=False,
    debug=False,
) -> None:
    if not pipe_dir:
        pipe_dir = os.path.join(os.getcwd(), LOCAL_PIPE_DIR)

    assert pipe_dir is not None
    assert isinstance(pipe_dir, str)
