# -*- encoding: utf-8 -*-
from threading import Thread
from multiprocessing import Process
import sys
import time
import logging


class Daemon:
    """class function descriptor for repeating
    task in backgorund, you can create both from
    class (@Daemon) and instance (@Daemon())
    """

    def __init__(
        self,
        task: callable = None,
        *,
        delay: float = 1.0,
        repeat: int = -1,
        process: bool = False
    ):
        """Can be used to configure Daemon by simply
        using @Daemon(kwargs) instead of @Daemon

        Args:
            task (callable, optional): Provided automaticly by python @dscp syntax. Defaults to None.
            delay (float, optional): Interval delay, affects response time. Defaults to 1.0.
            repeat (int, optional): defines whather task has to be repeated, how many times, infinitely if -1
            process (bool, optional): Specifies wheather Thread (default) or
                                    Process is going to be usedDefaults to False.
        """
        self._repeat = repeat
        self._delay = delay
        self._keepAlive = True
        self._daemon = None
        self._task = task
        self._stdout = sys.stdout
        self._provider = Process if process else Thread

    def __del__(self):
        if self._daemon is not None:
            self.join()
            self.kill()

    @property
    def repeatCount(self):
        """This method is a getter for _repeat
        attribute, which specifies how many times
        task should be repeated to be compleated

        Returns:
            int: task repeat count
        """
        return self._repeat

    @repeat.setter
    def repeatCount(self, value):
        """This method is a setter for _repeat attr

        Args:
            value (int): integet equal or above -1
        """
        if isinstance(value) and value >= -1:
            self._repeat = value

    @staticmethod
    def __daemon__(self, *args, **kwargs):
        """Static function managing execution loop
        of provided task
        """
        try:
            # Event loop can be stop by changing
            # self._keepAlive boolean flag
            repeat = self._repeat
            while self._keepAlive and repeat != 0:
                repeat -= 1
                self._task(*args, **kwargs)
                time.sleep(self._delay)
        except Exception as e:
            # in case of exception loop is exited and
            # exception is beening looged to stdout
            logging.basicConfig(stream=self._stdout)
            logging.exception(e, exc_info=True)

    def __call__(self, *args, **kwargs):
        """If this class is used as descriptor, calling its istance
        will spawn a thread executing given task,
        However if instance of this class is used as descriptor,
        first call of instance will set task function, and next
        one will spawn a thread. The point is, both class and
        instance can be used as descriptor

        Returns:
            self: this function return instance of Daemon descriptor
        """
        if self._task is None:
            if args and callable(args[0]):
                self._task = args[0]
            else:
                raise AttributeError(
                    "Daemon instance requires callable to be passed as an argument if none has been set in constructor"
                )
        else:
            # There can be only one daemon at once
            if self._daemon is None:
                # depending on wheather process=True have
                # been passed to constructior, provider
                # can be Process (if true) or Thread (else)
                self._daemon = self._provider(
                    target=Daemon.__daemon__, args=(self, *args), kwargs=kwargs
                )
                # Both Thread and Process have to be started manually
                self._daemon.start()
        return self

    def kill(self, wait: bool = False) -> bool:
        """This mehod sets keep alive flag to false,
        which means that deamon will exit before next
        iteration, but if deamon is a process one,
        termination will be delayed to the end of current
        iteration, otherwise it will exit immediately

        Args:
            wait (bool): determines wheather program should wait
                        until task terminates or force it to terminate
        Returns:
            bool: True if termination was immediate, False if not
        """
        if not wait and self._daemon is None:
            # deamon can be forced to die now, only
            # if it is a process, threads cannot be killed
            if isinstance(self._daemon, Process):
                # process have a method for instant killing
                self._daemon.kill()
                return True
            else:
                # set event loop flag to false, no more executions
                # will happen, but daemon can be alive for (delay) time
                self._keepAlive = False
                return False
        else:
            # wait for task to terminate
            return not self.join()

    def join(self):
        """This method calls daemons join method,
        if the daemon is preset, even if it is not
        alive (is dead or will terminate in next iteration)

        Returns:
            bool: True, if you were able to join daemon, False otherwise
        """
        if self._daemon is not None:
            self._daemon.join()
            return True
        return False

    def isAlive(self):
        """This method returns wheather current daemon
        is currently alive (and is not going to die in
        next iteration, if it is alive but is going to
        die, False will be returned)

        Returns:
            bool: True if alive, False otherwise
        """
        return self._keepAlive and self._daemon is not None and self._daemon.is_alive()

    def get(self):
        """Retrive descripted function

        Returns:
            [type]: [description]
        """
        return self._task

    def __enter__(self):
        """Implements context manager enter

        Returns:
            Daemon: this daemon
        """
        print("enter")
        if self._daemon is None:
            self()
        return self

    def __exit__(self, type, value, traceback):
        """Implements context manager exit
        Calls join() method and kill() method

        Args:
            type ([type]): [description]
            value ([type]): [description]
            traceback ([type]): [description]
        """
        print("exit")
        self.join()
        self.kill()
