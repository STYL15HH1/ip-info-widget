"""Storage and resource paths for installed and portable execution modes."""

from __future__ import annotations

import os
import sys
from pathlib import Path


class AppPaths:
    """Centralizes all paths so portable mode never leaks into UI code."""

    def __init__(self, portable: bool = False) -> None:
        self.portable = portable
        self.application_dir = self._application_dir()
        self.resource_dir = self._resource_dir()
        local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        self.data_dir = self.application_dir if portable else local_app_data / "MyIPWidget"

    @staticmethod
    def _application_dir() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[1]

    @staticmethod
    def _resource_dir() -> Path:
        if getattr(sys, "frozen", False):
            return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return Path(__file__).resolve().parents[1]

    @property
    def settings_path(self) -> Path:
        return (self.data_dir / "config" / "settings.json") if self.portable else self.data_dir / "settings.json"

    @property
    def history_path(self) -> Path:
        return (self.data_dir / "history" / "ip-history.json") if self.portable else self.data_dir / "ip-history.json"

    @property
    def flags_dir(self) -> Path:
        return self.resource_dir / "assets" / "images" / "flags"

    @property
    def app_icon_path(self) -> Path:
        return self.resource_dir / "assets" / "icons" / "ip-info-widget.ico"

    @property
    def author_image_path(self) -> Path:
        return self.resource_dir / "assets" / "author" / "styl15hh1.png"

    def ensure_data_directories(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)


def portable_requested(argv: list[str] | None = None) -> bool:
    arguments = sys.argv[1:] if argv is None else argv
    return "--portable" in arguments
