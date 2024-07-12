# -*- coding: utf-8 -*-

import os
from time import sleep, time
from typing import Optional


def wait_exists(path: str, timeout: Optional[float] = None, step=0.001) -> None:
    begin = time()
    while not os.path.exists(path):
        if timeout is not None and (time() - begin) > timeout:
            raise TimeoutError
        sleep(step)
