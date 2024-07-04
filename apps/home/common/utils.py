import logging
import time
from functools import wraps

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def log_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Starting function: {func.__name__}")
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Finished function: {func.__name__} in {duration:.2f} seconds")
        return result

    return wrapper
