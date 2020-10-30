# -*- encoding: utf-8 -*-
from threading import Thread, Event
import sys
import time
import logging


class Daemon:
    def __init__(self, task: callable = None, *, delay: float = 1.0, repeat: int = -1):
        self._repeat = repeat
        self._delay = delay
        self._callbacks = []
        self._thread = None
        self._dieFlag = Event()
        if task is not None:
            self.addCallback(task)

    def __daemon__(self, *args, **kwargs):
        try:
            repeat = self._repeat
            delta = 0
            while not self._dieFlag.wait(delta) and repeat != 0:
                repeat -= 1
                startTime = time.time()
                for func in self._callbacks:
                    func(*args, **kwargs)
                endTime = time.time()
                delta = startTime + self._delay - endTime
                if delta < 0:
                    delta = 0
        except Exception as e:
            logging.exception(e, exc_info=True)

    def __call__(self, *args, **kwargs):
        if not self._callbacks:
            if args and callable(args[0]):
                self.addCallback(args[0])
            else:
                raise ValueError("Missing callable.")
        else:
            if self._thread is None:
                self._setThread(args, kwargs)
                self._thread.start()
            else:
                raise RuntimeError("Thread is already alive!")
        return self

    def _setThread(self, args, kwargs):
        self._thread = Thread(target=self.__daemon__, args=args, kwargs=kwargs, daemon=True)

    def __iadd__(self, other):
        if callable(other):
            self.addCallback(other)
        elif isinstance(other, Daemon):
            self._callbacks.extend(other._callbacks)
        else:
            super().__iadd__(other)

    def addCallback(self, func: callable):
        self._callbacks.append(func)

    def kill(self):
        self._dieFlag.set()
        self._thread.join()
        self._dieFlag.clear()
        self._thread = None

    def getTasks(self):
        return self._callbacks

    def isAlive(self):
        return self._thread is not None and self._thread.is_alive()
