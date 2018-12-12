def generator():
    yield 1
    yield 2
    yield 3
    return 'finished'


def proxy():
    g = generator()
    msg = yield from g
    print(f'generator return values is: {msg}')


p = proxy()
while True:
    try:
        data = p.send(None)
        print(f'generator yield data is {data}')
    except StopIteration:
        break
