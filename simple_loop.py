from types import coroutine
from collections import defaultdict
from heapq import heappop, heappush
from timeit import default_timer as now
from time import sleep as _sleep
from functools import total_ordering
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE
import socket

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


class JoinAllEvent(Event):
    def __init__(self, *coros):
        self.coros = coros


class SleepEvent(Event):
    def __init__(self, seconds):
        self.wakeup_time = seconds + now()


class ReadEvent(Event):
    def __init__(self, stream):
        self.stream = stream


class WriteEvent(Event):
    def __init__(self, stream):
        self.stream = stream


@coroutine
def spawn(coro):
    future = yield SpawnEvent(coro)
    return future


@coroutine
def join(future):
    result = yield JoinEvent(future)
    return result


@coroutine
def joinall(*futures):
    result = yield JoinAllEvent(*futures)
    return result


@coroutine
def sleep(seconds):
    yield SleepEvent(seconds)


@coroutine
def receive(stream, chunk_size):
    yield ReadEvent(stream)
    return stream.recv(chunk_size)


@coroutine
def send(stream, data):
    while data:
        yield WriteEvent(stream)
        chunk_size = stream.send(data)
        data = data[chunk_size:]


async def main_coro():
    future1 = await spawn(sleep(3))
    future2 = await spawn(sleep(4))
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


class MultiCoroWrapper:
    def __init__(self, coros):
        self.coros = coros
        self.results = {}

    def set_result(self, coro, result):
        self.results[coro] = result

    @property
    def all_done(self):
        return len(self.coros) == len(self.results)

    @property
    def result(self):
        return (self.results[coro] for coro in self.coros)


def run_until_complete(coro):
    tasks = [Task(coro, None)]
    join_watcher = defaultdict(list)
    joinall_watcher = defaultdict(list)
    multi_coro_wrappers = dict()
    delayed_tasks = []
    selector = DefaultSelector()
    ret = None
    while tasks or delayed_tasks or selector.get_map():
        if not tasks:
            if delayed_tasks:
                timeout = max((0.0, delayed_tasks[0].wakeup_time - now()))
            else:
                timeout = None
            if selector.get_map():
                for key, events in selector.select(timeout):
                    tasks.append(Task(key.data, None))
                    selector.unregister(key.fileobj)
            else:
                _sleep(timeout)
        while delayed_tasks and delayed_tasks[0].wakeup_time < now():
            task = heappop(delayed_tasks)
            tasks.append(task)
        queue, tasks = tasks, []
        for task in queue:
            try:
                res = task.coro.send(task.trigger)
            except StopIteration as e:
                ret = e.value
                tasks.extend(Task(join_coro, e.value) for join_coro in join_watcher.pop(task.coro, []))
                for joinall_coro in joinall_watcher.pop(task.coro, []):
                    wrapper = multi_coro_wrappers[joinall_coro]
                    wrapper.set_result(task.coro, e.value)
                    if wrapper.all_done:
                        tasks.append(Task(joinall_coro, wrapper.result))
            else:
                if isinstance(res, SpawnEvent):
                    tasks.append(Task(res.coro, None))
                    tasks.append(Task(task.coro, res.coro))
                elif isinstance(res, JoinEvent):
                    join_watcher[res.coro].append(task.coro)
                elif isinstance(res, JoinAllEvent):
                    for coro in res.coros:
                        joinall_watcher[coro].append(task.coro)
                    multi_coro_wrappers[task.coro] = MultiCoroWrapper(res.coros)
                elif isinstance(res, SleepEvent):
                    heappush(delayed_tasks, Task(task.coro, None, wakeup_time=res.wakeup_time))
                elif isinstance(res, WriteEvent):
                    selector.register(res.stream, EVENT_WRITE, task.coro)
                elif isinstance(res, ReadEvent):
                    selector.register(res.stream, EVENT_READ, task.coro)
                else:
                    tasks.append(task)
    return ret


if __name__ == '__main__':
    with timer():
        print(list(run_until_complete(main_coro())))
