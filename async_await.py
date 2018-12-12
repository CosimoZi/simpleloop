from types import coroutine


@coroutine
def generator():
    yield 1
    yield 2
    yield 3
    return 'finished'


async def proxy():
    g = generator()
    msg = await g
    print(f'generator return values is: {msg}')


if __name__ == '__main__':
    p = proxy()
    while True:
        try:
            data = p.send(None)
            print(f'generator yield data is {data}')
        except StopIteration:
            break
