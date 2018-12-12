from types import coroutine
from inspect import iscoroutine


@coroutine
def hello_world():
    yield 'h'
    yield 'e'
    yield 'l'
    yield 'l'
    yield 'o'
    return 'world'


@coroutine
def spawn(coro):
    yield coro


async def main_coro():
    await spawn(hello_world())
    print('ok')


class Task:
    def __init__(self, coro, trigger):
        self.coro = coro
        self.trigger = trigger


def run_until_complete(coro):
    tasks = [Task(coro, None)]
    while tasks:
        queue, tasks = tasks, []
        for task in queue:
            try:
                res = task.coro.send(task.trigger)
            except StopIteration:
                pass
            else:
                if iscoroutine(res):
                    tasks.append(Task(res, None))
                tasks.append(task)


if __name__ == '__main__':
    run_until_complete(main_coro())
