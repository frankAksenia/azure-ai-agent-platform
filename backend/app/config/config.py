from pathlib import Path

import yaml


def load_config(path: str | None = None) -> dict:
    if path is None:
        path = Path(__file__).resolve().parents[3] / "config.yaml"
    else:
        path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}
