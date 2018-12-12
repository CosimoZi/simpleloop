from types import coroutine
from collections import defaultdict


@coroutine
def hello_world():
    yield 'h'
    yield 'e'
    yield 'l'
    yield 'l'
    yield 'o'
    return 'world'


class Event:
    def __init__(self, coro):
        self.coro = coro


class SpawnEvent(Event):
    pass


class JoinEvent(Event):
    pass


@coroutine
def spawn(coro):
    yield SpawnEvent(coro)


@coroutine
def join(future):
    result = yield JoinEvent(future)
    return result


async def main_coro():
    future = await spawn(hello_world())
    result = await join(future)
    return result


class Task:
    def __init__(self, coro, trigger):
        self.coro = coro
        self.trigger = trigger


def run_until_complete(coro):
    tasks = [Task(coro, None)]
    watcher = defaultdict(list)
    while tasks:
        queue, tasks = tasks, []
        for task in queue:
            try:
                res = task.coro.send(task.trigger)
            except StopIteration as e:
                tasks.extend(Task(coro, e.value) for coro in watcher.pop(task, []))
            else:
                if isinstance(res, SpawnEvent):
                    tasks.append(Task(res.coro, None))
                    tasks.append(task)
                elif isinstance(res, JoinEvent):
                    watcher[].append(task.coro)


if __name__ == '__main__':
    print(run_until_complete(main_coro()))
