from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging() -> None:
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger("mcp_guard")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = RotatingFileHandler(
        "logs/mcp-guard.log", maxBytes=1_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console)
