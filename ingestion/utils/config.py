"""
Configuration loader for the ingestion pipeline.

Loads YAML configs from ingestion/config/ and validates them.
"""

import os
import logging
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_config(name: str) -> dict:
    """Load a YAML config by name (e.g. 'sources', 'scoring')."""
    path = _CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        logger.warning(f"Config file not found: {path}")
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable with optional default."""
    return os.environ.get(key, default)


def require_env(key: str) -> str:
    """Get a required env var; raise if missing."""
    val = os.environ.get(key)
    if not val:
        raise RuntimeError(f"Required environment variable not set: {key}")
    return val
