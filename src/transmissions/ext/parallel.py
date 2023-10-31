"""
Extensions to Twisted for managing parallel workloads.

An example::

    from twisted.logger import Logger

    log = Logger()

    async def countInParallel():
        async def logValue(value):
            log.info("value = {value}", value=value)

        def count():
            i = 0
            while True:
                i += 1
                yield i

        # Generate a stream of asynchronous tasks
        tasks = (logValue(i) for i in count())

        # Keep track of how long each task is taking via log events
        tasks = timeTasks(tasks, log)

        # Limit the rate at which events are processed to 32 per second
        tasks = rateLimited(tasks, maxRate=32)

        # Run the tasks in parallel, running up to 8 tasks simultaneously
        await runInParallel(tasks, maxTasks=8)
"""

from collections.abc import Awaitable, Iterable
from random import random
from time import time
from typing import Any, cast

from attr import attrib, attrs
from twisted.internet.defer import Deferred, DeferredList, ensureDeferred
from twisted.internet.interfaces import IReactorTime
from twisted.internet.task import Cooperator, deferLater
from twisted.logger import Logger, LogLevel


__all__ = ("runInParallel",)


log = Logger()


@attrs(auto_attribs=True, kw_only=True, frozen=True)
class RunningAverage:
    """
    Keeps a running count/total/average of floats.
    """

    @attrs(auto_attribs=True, kw_only=True, eq=False)
    class _State:
        """
        Internal mutable state for OktaClient.
        """

        count = 0
        total = 0.0

    _state: _State = attrib(factory=_State, init=False)

    def __str__(self) -> str:
        return (
            f"average {self.average:f}"
            f" of {self.count} values"
            f" totaling {self.total:f}"
        )

    @property
    def count(self) -> float:
        """
        Total count of inputs so far.
        """
        return self._state.count

    @property
    def total(self) -> float:
        """
        Total sum of inputs so far.
        """
        return self._state.total

    @property
    def average(self) -> float:
        """
        Average of inputs so far.
        """
        return self.total / self.count

    def append(self, value: float) -> None:
        """
        Add a value to the values being averaged.
        """
        self._state.count += 1
        self._state.total += value


def timeTasks(
    tasks: Iterable[Awaitable],
    logger: Logger,
    logLevel: LogLevel = LogLevel.info,
) -> Iterable[Awaitable]:
    """
    Time the execution of tasks and emit that information via the given logger,
    at the given log level.
    """
    startTime = time()
    taskAverageTime = RunningAverage()

    async def timeTask(task: Awaitable) -> None:
        taskStartTime = time()
        await task
        taskDuration = time() - taskStartTime
        taskAverageTime.append(taskDuration)
        logger.emit(
            logLevel,
            "Task execution time: {duration:f}, {average}",
            duration=taskDuration,
            average=taskAverageTime,
        )
        totalDuration = time() - startTime
        logger.emit(
            logLevel,
            "Total execution time: {duration:f}, rate: {rate:f}",
            duration=totalDuration,
            rate=taskAverageTime.count / totalDuration,
        )

    return (timeTask(task) for task in tasks)


def rateLimited(
    tasks: Iterable[Awaitable],
    maxRate: int,
    *,
    timeWindow: float = 2.0,
) -> Iterable[Awaitable]:
    """
    Limits the processing rate of tasks to a maximum number of tasks per second
    within a rolling time window of a given size (in seconds).
    """
    from twisted.internet import reactor

    maxPerWindow = maxRate * timeWindow

    processed: list[float] = []

    def taskCount() -> int:
        nonlocal processed

        # Remove tasks that were processed prior to the rolling window.
        expiredTime = time() - timeWindow
        for index in range(len(processed)):
            if processed[index] > expiredTime:
                processed = processed[index:]
                break
        else:
            processed = []

        assert len(processed) <= maxPerWindow, len(processed)
        return len(processed)

    for task in tasks:
        while True:
            if taskCount() >= maxPerWindow:
                # Stall for a random time interval up to one time window
                yield deferLater(
                    cast(IReactorTime, reactor), random() * timeWindow
                )
            else:
                processed.append(time())
                yield task
                break


async def runInParallel(
    tasks: Iterable[Deferred[Any]],
    *,
    maxTasks: int = 32,
) -> None:
    """
    Schedule tasks to run in parallel, up to maxTasks at a time.

    Tasks are given as an iterable of deferreds (or deferred-yielding
    coroutines) which fire as each task completes.
    """
    cooperator = Cooperator()

    tasks = (ensureDeferred(task) for task in tasks)

    # Use a DeferredList to schedule maxTasks CooperativeTasks (via the
    # Cooperator) that draw from the given work items.
    await DeferredList(cooperator.coiterate(tasks) for i in range(maxTasks))
