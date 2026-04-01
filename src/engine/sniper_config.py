"""Configuration loading for the sniper engine."""

import json

from src.utils.constants import CONFIG_PATH, DEV_PATH
from src.utils.logger import log_error


def load_system_config():
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as exc:
        log_error(f"Config load failed: {exc}")
        return {}


CONF = load_system_config()
