"""Configuration de la journalisation de SysWatch-API."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


def setup_logger(config: dict[str, Any]) -> logging.Logger:
    """Configure les journaux console et fichier.

    Args:
        config: Paramètres de configuration du projet.

    Returns:
        logging.Logger: Journal configuré.
    """
    settings = config["logging"]
    log_path = Path(settings["file"])
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("SysWatch")
    logger.setLevel(settings["level"])
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=settings["max_bytes"],
        backupCount=settings["backup_count"],
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger