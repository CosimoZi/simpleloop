from types import coroutine
from collections import defaultdict
from heapq import heappop, heappush
from timeit import default_timer as now
from time import sleep as _sleep
from functools import total_ordering
from itertools import chain
from weakref import WeakKeyDictionary

from timer import timer


@coroutine
def hello_world():
    yield 'h'
    yield 'e'
    yield 'l'
    yield 'l'
    yield 'o'
    return 'world'


class Event:
    pass


class SpawnEvent(Event):
    def __init__(self, coro):
        self.coro = coro


class JoinEvent(Event):
    def __init__(self, future):
        self.future = future


class SleepEvent(Event):
    def __init__(self, seconds):
        self.wakeup_time = seconds + now()


@coroutine
def spawn(coro):
    future = yield SpawnEvent(coro)
    return future


@coroutine
def join(future):
    result = yield JoinEvent(future)
    return result


async def joinall(*futures):
    future = Future(*chain(*(f.coros for f in futures)))
    result = await join(future)
    return result


@coroutine
def sleep(seconds):
    yield SleepEvent(seconds)
    return seconds


async def main_coro():
    future1 = await spawn(sleep(1))
    future2 = await spawn(sleep(2))
    result = await joinall(future1, future2)
    return result


@total_ordering
class Task:
    def __init__(self, coro, trigger, wakeup_time=None):
        self.coro = coro
        self.trigger = trigger
        self.wakeup_time = wakeup_time if wakeup_time else now()

    def __lt__(self, other):
        return self.wakeup_time < other.wakeup_time


class Future:
    def __init__(self, *coros):
        self.coros = coros
        self.results = {}

    def set_result(self, coro, result):
        self.results[coro] = result

    @property
    def all_done(self):
        return len(self.coros) == len(self.results)

    @property
    def result(self):
        if len(self.coros) == 1:
            return self.results[self.coros[0]]
        return [self.results[coro] for coro in self.coros]


def run_until_complete(coro):
    tasks = [Task(coro, None)]
    watcher = defaultdict(list)
    future_finder = WeakKeyDictionary()
    delayed_tasks = []
    ret = None
    while tasks or delayed_tasks:
        if not tasks:
            _sleep(max((0.0, delayed_tasks[0].wakeup_time - now())))
        while delayed_tasks and delayed_tasks[0].wakeup_time < now():
            task = heappop(delayed_tasks)
            tasks.append(task)
        queue, tasks = tasks, []
        for task in queue:
            try:
                res = task.coro.send(task.trigger)
            except StopIteration as e:
                # tasks.extend(Task(join_coro, e.value) for join_coro in join_watcher.pop(task.coro, []))
                ret = e.value
                future = future_finder.get(task.coro)
                if future:
                    future.set_result(task.coro, e.value)
                    if future.all_done:
                        for coro in watcher.pop(future, []):
                            tasks.append(Task(coro, future.result))
            else:
                if isinstance(res, SpawnEvent):
                    tasks.append(Task(res.coro, None))
                    tasks.append(Task(task.coro, Future(res.coro)))
                elif isinstance(res, JoinEvent):
                    watcher[res.future].append(task.coro)
                    for coro in res.future.coros:
                        future_finder[coro] = res.future
                elif isinstance(res, SleepEvent):
                    heappush(delayed_tasks, Task(task.coro, None, wakeup_time=res.wakeup_time))
                else:
                    tasks.append(task)
    return ret


if __name__ == '__main__':
    with timer():
        print(run_until_complete(main_coro()))
