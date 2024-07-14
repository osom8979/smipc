# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from threading import Event, Thread
from typing import Optional

from smipc.decorators.override import override
from smipc.protocols.base import ProtocolInterface, WrittenInfo


class ProtocolThreadInterface(ABC):
    @abstractmethod
    def on_recv(self, data: bytes) -> None:
        raise NotImplementedError


class ProtocolThread(Thread, ProtocolThreadInterface):
    def __init__(
        self,
        proto: ProtocolInterface,
        name: Optional[str] = None,
        event: Optional[Event] = None,
    ):
        super().__init__(group=None, name=name)
        self._proto = proto
        self._event = event if event is not None else Event()

    @override
    def run(self) -> None:
        while not self._event.is_set():
            data = self._proto.recv()
            if data is not None:
                self.on_recv(data)

    @override
    def on_recv(self, data: bytes) -> None:
        pass

    def done(self) -> None:
        self._event.set()

    def close(self) -> None:
        self._proto.close()

    def cleanup(self) -> None:
        self._proto.cleanup()

    def send(self, data: bytes) -> WrittenInfo:
        return self._proto.send(data)
