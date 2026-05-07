import logging
import sys
from pathlib import Path
from colorlog import ColoredFormatter

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
COLOR_FORMATS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}
console_formatter = ColoredFormatter(
    "%(log_color)s[%(asctime)s] %(levelname)-8s%(reset)s %(blue)s%(message)s",
    datefmt="%H:%M:%S",
    log_colors=COLOR_FORMATS,
    secondary_log_colors={},
    style="%",
)
file_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("tocco")
logger.setLevel(logging.DEBUG)

logger.handlers.clear()

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(LOGS_DIR / "tocco.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logging.getLogger("django").setLevel(logging.WARNING)
logging.getLogger("django.request").setLevel(logging.WARNING)
logging.getLogger("django.db.backends").setLevel(logging.WARNING)
logging.getLogger("celery").setLevel(logging.WARNING)
logging.getLogger("redis").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name):
    """Получить логгер для конкретного модуля"""
    return logging.getLogger(f"tocco.{name}")
