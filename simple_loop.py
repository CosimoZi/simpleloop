from types import coroutine


@coroutine
def hello_world():
    yield 'h'
    yield 'e'
    yield 'l'
    yield 'l'
    yield 'o'
    return 'world'


async def task():
    ret = await hello_world()
    return ret


def run_until_complete(task):
    while True:
        try:
            task.send(None)
        except StopIteration as e:
            return e.value


if __name__ == '__main__':
    print(run_until_complete(task()))
