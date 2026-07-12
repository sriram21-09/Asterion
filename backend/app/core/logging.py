import logging
import sys
import time
from contextlib import contextmanager
from app.core.config import settings

def setup_logging():
    log_level_name = settings.log_level.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    logger = logging.getLogger("asterion")
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # Standard logging format with timestamp, level, and logger name
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger = setup_logging()

@contextmanager
def log_execution_time(action_name: str, logger_to_use=None):
    """Context manager to measure and log the execution time of a code block."""
    if logger_to_use is None:
        logger_to_use = logger
    start_time = time.time()
    yield
    duration = time.time() - start_time
    logger_to_use.info(f"{action_name} completed in {duration:.4f}s")
