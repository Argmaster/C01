# -*- encoding: utf-8 -*-
from threading import Thread, Event
import sys
import time
import logging
from typing import Callable, Tuple, Union


class DaemonLeaveException(Exception):
    pass


class Daemon:
    def __init__(
        self,
        task: Callable = None,
        *,
        delay: float = 1.0,
        repeat: int = -1,
        tasks: Tuple[Callable] = None,
        callbacks: Tuple[Callable] = None,
    ):
        """Daemon class which can be used as a descriptor both as a class and as intance
        to simply create thread daemon function(s) to be executed in single or multiple
        times, with callback after termination

        Args:
            task (callable, optional): first task to be added to task list, can be passed in call. Defaults to None.
            delay (float, optional): delay between each execution of task. Defaults to 1.0.
            repeat (int, optional): defines how many times to repeat task loop, -1 means infinitely. Defaults to -1.
            tasks (tuple or list, optional): tasks to extend task list (repeat periodically)
            callbacks (tuple or list, optional): callbacks to extend callbacks list (execute after termination of task loop)
        """
        self._repeat = repeat
        self._delay = delay
        self._tasks = []
        self._callbacks = []
        self._thread = None
        self._dieFlag = Event()
        #self._tasks.append(func) if callable(func) else None
        self._tasks.append(tasks) if isinstance(tasks, (tuple, list)) else None
        self._callbacks.append(callbacks) if isinstance(callbacks, (tuple, list)) else None

    def __daemon__(self, *args, **kwargs):
        """Daemon tasks loop, with checking for termination flag

        Raises:
            DaemonLeaveException: Raised to leave a loop, shouldn't ever leave this function
        """
        try:
            repeatCount = self._repeat
            delta = 0
            while True:
                # first condition is used to wait for delta seconds and terminate on signal
                # second one makes daemon leave after n repetitions
                if self._dieFlag.wait(delta) or repeatCount == 0:
                    raise DaemonLeaveException()
                # decement repeat count, leave it as is if -1 -> infinite execution
                repeatCount = repeatCount - 1 if repeatCount > 0 else repeatCount
                # get start time of execution, to calc how to wait then
                startTime = time.time()
                # loop through all callbacks
                for func in self._tasks:
                    # before execution test if exit flag is set
                    if self._dieFlag.isSet():
                        raise DaemonLeaveException()
                    func(*args, **kwargs)
                # calculate how long to wait before next execution
                delta = startTime + self._delay - time.time()
                delta = delta if delta > 0 else 0
        except DaemonLeaveException:
            # this exception is just a signl to end
            for callback in self._callbacks:
                callback(*args, **kwargs)
        except Exception as e:
            # log exeption if unusual
            logging.exception(e, exc_info=True)

    def __call__(self, *args, **kwargs):
        """If instance of Daemon is used as descriptor
        (no function has been passed to constructior)
        first execution of this fuction is expecting
        a callable to be passed as argument,
        Every next call and every call if Daemon class
        was used as descriptor will run daemon tasks thread
        if there is no already running

        Raises:
            ValueError: if there is no callable to execute
            RuntimeError: if there is already a running thread

        Returns:
            self: this instance of daemon
        """
        if not self._tasks:
            if args and callable(args[0]):
                self.addTask(args[0])
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
        """Set self._thread to new thread object
        args and kwargs will be passed to it

        Args:
            args (tuple): args to be passed to thread
            kwargs (dict): kwargs to be passed to thread
        """
        if self._thread is None:
            self._thread = Thread(
                target=self.__daemon__, args=args, kwargs=kwargs, daemon=True
            )
        else:
            raise RuntimeError("Thread cannot be overwriten")

    def __iadd__(self, other: Union[Callable, "Daemon"]):
        """Add callable to tasks or extend tasks by
        tasks from another Daemon

        Args:
            other (callable or Daemon): task to be added
        """
        if callable(other):
            self.addTask(other)
        elif isinstance(other, Daemon):
            self._tasks.extend(other._tasks)
        else:
            super().__iadd__(other)

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(f"Invalid delay value type: {type(value)}")
        else:
            self._delay = value

    def addCallback(self, func: Callable):
        """Insert callback into callback list,
        it will be called after task loop finishes,
        but only if no unexpected exception will ocure

        Args:
            func (callable): function to be added, will recive
                            same arguments as each task (passed while
                            daemon is called)
        """
        self._callbacks.append(func)

    def addTask(self, func: Callable):
        """Insert task into task list, it will be
        called periodically every <delay> seconds

        Args:
            func (callable): function to be added, will recive
                            same arguments as each task (passed while
                            daemon is called)
        """
        self._tasks.append(func)

    def kill(self, wait: bool = True):
        """Set termination flag for thread, and wait until it terminates"""
        self._dieFlag.set()
        while self._thread.isAlive() and wait:
            time.sleep(0.01)
        self._dieFlag.clear()
        self._thread = None

    def getTasks(self):
        """Retrive list of tasks provided for this daemon

        Returns:
            [list]: task list
        """
        return self._tasks

    def isAlive(self):
        """Returns wheater thread exists and is alive,
        true if both, false otherise

        Returns:
            bool: True if alive, false otherwise
        """
        return self._thread is not None and self._thread.is_alive()
