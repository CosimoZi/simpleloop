from types import coroutine
from collections import defaultdict
from heapq import heappop, heappush
from timeit import default_timer as now
from time import sleep as _sleep

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
    def __init__(self, coro):
        self.coro = coro


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


@coroutine
def sleep(seconds):
    yield SleepEvent(seconds)


async def main_coro():
    future = await spawn(hello_world())
    result = await join(future)
    with timer():
        await sleep(3)
    with timer():
        await sleep(2)
    return result


class Task:
    def __init__(self, coro, trigger, wakeup_time=None):
        self.coro = coro
        self.trigger = trigger
        self.wakeup_time = wakeup_time if wakeup_time else now()

    def __cmp__(self, other):
        return self.wakeup_time - other.wakeup_time


def run_until_complete(coro):
    tasks = [Task(coro, None)]
    watcher = defaultdict(list)
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
                ret = e.value
                tasks.extend(Task(join_coro, e.value) for join_coro in watcher.pop(task.coro, []))
            else:
                if isinstance(res, SpawnEvent):
                    tasks.append(Task(res.coro, None))
                    tasks.append(Task(task.coro, res.coro))
                elif isinstance(res, JoinEvent):
                    watcher[res.coro].append(task.coro)
                elif isinstance(res, SleepEvent):
                    heappush(delayed_tasks, Task(task.coro, None, wakeup_time=res.wakeup_time))
                else:
                    tasks.append(task)
    return ret


if __name__ == '__main__':
    with timer():
        print(run_until_complete(main_coro()))
