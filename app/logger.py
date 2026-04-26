
import logging
import os

from app.config import PROJECT_ROOT

# ----------------------------
# Logging setup
# ----------------------------
dir_path = PROJECT_ROOT

import logging
import os

DEFAULT_LOGGING_PATH = "validation.log"


logger = logging.getLogger("my_app")
logger.setLevel(logging.INFO)

_handler = None


def set_logging(path: str = None):
    global _handler

    log_path = os.path.join(dir_path, "csv", path or DEFAULT_LOGGING_PATH)

    # Ensure folder exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Remove old handler
    if _handler:
        logger.removeHandler(_handler)
        _handler.close()

    # Create new handler
    _handler = logging.FileHandler(log_path)
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    ))

    logger.addHandler(_handler)
