import sys
from loguru import logger

# Fix Windows console encoding (CP1256 → UTF-8)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Remove default handler
logger.remove()

# Console: human-readable, colored
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

# File: full detail
logger.add(
    "enjazi.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
    level="DEBUG",
    rotation="5 MB",
    retention="7 days",
    encoding="utf-8",
)

__all__ = ["logger"]
