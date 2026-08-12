"""Versioned settings storage with backward-compatible defaults."""

from __future__ import annotations

import json
from copy import deepcopy

from core.storage import AppPaths


CONFIG_VERSION = 2
DEFAULTS: dict[str, object] = {
    "config_version": CONFIG_VERSION,
    "theme": "dark",
    "opacity": 0.92,
    "refresh_seconds": 5,
    "show_location": True,
    "show_isp": False,
    "monitor_device": None,
    "ping_host": "1.1.1.1",
    "ping_enabled": False,
    "autostart": False,
    "always_on_top": True,
    "display_mode": "normal",
    "x": None,
    "y": None,
}
DISPLAY_MODES = ("compact", "normal", "monitoring")


class SettingsManager:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths
        self.data = self.load()

    def load(self) -> dict[str, object]:
        try:
            loaded = json.loads(self.paths.settings_path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("settings must be an object")
        except (OSError, ValueError, json.JSONDecodeError):
            loaded = {}
        values = {**deepcopy(DEFAULTS), **loaded}
        values["config_version"] = CONFIG_VERSION
        if values.get("display_mode") not in DISPLAY_MODES:
            values["display_mode"] = "normal"
        values["refresh_seconds"] = max(5, _as_int(values.get("refresh_seconds"), 5))
        values["opacity"] = max(0.55, min(1.0, _as_float(values.get("opacity"), 0.92)))
        return values

    def update(self, values: dict[str, object]) -> None:
        self.data.update(values)
        self.data["config_version"] = CONFIG_VERSION
        self.data["refresh_seconds"] = max(5, _as_int(self.data.get("refresh_seconds"), 5))
        self.data["opacity"] = max(0.55, min(1.0, _as_float(self.data.get("opacity"), 0.92)))
        if self.data.get("display_mode") not in DISPLAY_MODES:
            self.data["display_mode"] = "normal"

    def save(self) -> None:
        self.paths.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.settings_path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")


def _as_int(value: object, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _as_float(value: object, default: float) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
