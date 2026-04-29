"""Configuration and auth storage."""
from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

CONFIG_DIR = Path.home() / ".easywheels"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_API_URL = "https://easywheels.io"


def load_config() -> dict:
    """Load config from ~/.easywheels/config.toml."""
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "rb") as f:
        return tomllib.load(f)


def _toml_encode_value(value: object) -> str:
    """Encode a single value as a TOML literal."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    return repr(value)


def save_config(data: dict) -> None:
    """Save config to ~/.easywheels/config.toml."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f"{key} = {_toml_encode_value(value)}" for key, value in data.items()]
    CONFIG_FILE.write_text("\n".join(lines) + "\n")


def get_api_key() -> str | None:
    """Get API key from env var or config file."""
    import os
    return os.environ.get("EASYWHEELS_API_KEY") or load_config().get("api_key")


def get_api_url() -> str:
    """Get API base URL."""
    cfg = load_config()
    return cfg.get("api_url", DEFAULT_API_URL)


def set_api_key(key: str) -> None:
    """Store API key."""
    cfg = load_config()
    cfg["api_key"] = key
    save_config(cfg)


def set_api_url(url: str) -> None:
    """Store custom API URL."""
    cfg = load_config()
    cfg["api_url"] = url
    save_config(cfg)
