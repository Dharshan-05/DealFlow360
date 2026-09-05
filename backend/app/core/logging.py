import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure minimal, structured application logger."""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("dealflow360")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
    return logger


logger = setup_logging()
