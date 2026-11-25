"""Gestion de la configuration de SysWatch-API."""

import json
from pathlib import Path
from typing import Any


def load_config() -> dict[str, Any]:
    """Charge les paramètres de configuration.

    Returns:
        dict: Paramètres du projet.
    """
    config_path = Path(__file__).resolve().parent.parent / "config.json"

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)