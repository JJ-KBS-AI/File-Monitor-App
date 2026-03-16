from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional

from .config import DEFAULT_INTERVAL, PRESET_FILE


@dataclass
class PresetData:
    paths: List[str]
    extensions: List[str]
    interval: int = DEFAULT_INTERVAL


def load_preset(path: str = PRESET_FILE) -> Optional[PresetData]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return PresetData(
        paths=data.get("paths", []),
        extensions=data.get("extensions", []),
        interval=int(data.get("interval", DEFAULT_INTERVAL)),
    )


def save_preset(preset: PresetData, path: str = PRESET_FILE) -> None:
    data = {
        "paths": preset.paths,
        "extensions": list(preset.extensions),
        "interval": int(preset.interval),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

