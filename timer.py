import sys
import logging
from timeit import default_timer
from contextlib import contextmanager

logger = logging.getLogger('TIMER')
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s'))
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)


@contextmanager
def timer():
    t1 = default_timer()
    try:
        yield
    finally:
        t2 = default_timer()
        logger.debug(f'{t2-t1} seconds')
