"""Load and save the YAML configuration used by the pipeline."""

from pathlib import Path

import yaml

from ..models.config import Config


def load_config(path: str | Path) -> Config:
    """Load a Config from a YAML file, or return defaults if it does not exist."""
    p = Path(path)
    if not p.exists():
        return Config()
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return Config.from_dict(data)


def save_config(config: Config, path: str | Path) -> None:
    """Serialize a Config to a YAML file (creating parent dirs as needed)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        yaml.safe_dump(config.to_dict(), f, sort_keys=False, allow_unicode=True)
