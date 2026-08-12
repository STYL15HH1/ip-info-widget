"""Optional system-tray integration; it deliberately uses the app icon, not flags."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw

try:
    import pystray
except ImportError:
    pystray = None


class TrayController:
    def __init__(self, app_name: str, icon_path: Path, show: Callable[[], None], hide: Callable[[], None], refresh: Callable[[], None], quit_app: Callable[[], None]) -> None:
        self.app_name = app_name
        self._callbacks = {"show": show, "hide": hide, "refresh": refresh, "quit": quit_app}
        self.icon = None
        self._image = self._load_icon(icon_path)

    def _load_icon(self, path: Path) -> Image.Image:
        try:
            with Image.open(path) as source:
                image = source.convert("RGBA")
            image.thumbnail((64, 64), Image.Resampling.LANCZOS)
            return image
        except (OSError, ValueError):
            image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse((4, 4, 60, 60), fill="#3478F6")
            draw.text((25, 19), "IP", fill="white")
            return image

    def start(self) -> None:
        if pystray is None:
            return
        self.icon = pystray.Icon("IPInfoWidget", self._image, self.app_name, self._menu())
        self.icon.run_detached()

    def _menu(self):
        return pystray.Menu(
            pystray.MenuItem("Show widget", lambda *_: self._callbacks["show"]()),
            pystray.MenuItem("Hide widget", lambda *_: self._callbacks["hide"]()),
            pystray.MenuItem("Refresh now", lambda *_: self._callbacks["refresh"]()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda *_: self._callbacks["quit"]()),
        )

    def set_ip(self, ip: str | None) -> None:
        if self.icon is not None:
            self.icon.icon = self._image
            self.icon.title = f"{self.app_name} — {ip or ''}".rstrip(" —")

    def stop(self) -> None:
        if self.icon is not None:
            self.icon.stop()
