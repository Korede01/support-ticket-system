import logging
from logging.handlers import TimedRotatingFileHandler
import os

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")

# Formatter
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# File handler - rotates daily
file_handler = TimedRotatingFileHandler(
    LOG_FILE_PATH, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.ERROR)  # Only log errors and above to file

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)  # Info and above to console

# Main logger
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)  # Capture all levels
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False
