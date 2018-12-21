import asyncio

import requests

from timer import timer


async def fetch_text():
    return requests.get('http://127.0.0.1:8000').text


if __name__ == '__main__':
    with timer():
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*[fetch_text() for _ in range(5)]))
