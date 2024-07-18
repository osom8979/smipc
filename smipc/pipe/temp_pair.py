# -*- coding: utf-8 -*-

import os
from os import PathLike
from typing import Union

from smipc.pipe.temp import TemporaryPipe
from smipc.variables import DEFAULT_FILE_MODE


class TemporaryPipePair:
    def __init__(
        self,
        s2c_path: Union[str, bytes, PathLike[str], PathLike[bytes]],
        c2s_path: Union[str, bytes, PathLike[str], PathLike[bytes]],
        mode=DEFAULT_FILE_MODE,
    ):
        if os.path.abspath(s2c_path) == os.path.abspath(c2s_path):
            raise ValueError("The 's2c_path' and 'c2s_path' cannot be the same")

        if os.path.exists(s2c_path):
            raise FileExistsError(f"s2c file already exists: '{s2c_path!r}'")
        if os.path.exists(c2s_path):
            raise FileExistsError(f"c2s file already exists: '{c2s_path!r}'")

        self._s2c = TemporaryPipe(s2c_path, mode=mode)
        self._c2s = TemporaryPipe(c2s_path, mode=mode)

        assert self._s2c.path == s2c_path
        assert self._c2s.path == c2s_path

        assert os.path.exists(s2c_path)
        assert os.path.exists(c2s_path)

    @property
    def s2c_path(self):
        return self._s2c.path

    @property
    def c2s_path(self):
        return self._c2s.path

    def cleanup(self):
        self._s2c.cleanup()
        self._c2s.cleanup()

    def __repr__(self):
        return "<{} s2c={!r} c2s={!r}>".format(
            self.__class__.__name__,
            self._s2c.path,
            self._c2s.path,
        )

    def __enter__(self):
        return self._s2c.path, self._c2s.path

    def __exit__(self, exc, value, tb):
        self.cleanup()
