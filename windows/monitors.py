"""Windows virtual-desktop monitor discovery and placement helpers."""

from __future__ import annotations

import ctypes
from ctypes import wintypes


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", ctypes.c_wchar * 32),
    ]


def list_monitors() -> list[dict[str, object]]:
    if not hasattr(ctypes, "windll"):
        return []
    monitors: list[dict[str, object]] = []
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)

    def callback(handle, _hdc, _rect, _data):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(info)
        if user32.GetMonitorInfoW(handle, ctypes.byref(info)):
            number = len(monitors) + 1
            primary = bool(info.dwFlags & 1)
            width = info.rcWork.right - info.rcWork.left
            height = info.rcWork.bottom - info.rcWork.top
            monitors.append({
                "device": info.szDevice,
                "label": f"Monitor {number}{' (primary)' if primary else ''} — {width}×{height}",
                "left": info.rcWork.left,
                "top": info.rcWork.top,
                "right": info.rcWork.right,
                "bottom": info.rcWork.bottom,
                "primary": primary,
            })
        return True

    monitor_callback = callback_type(callback)
    user32.EnumDisplayMonitors(None, None, monitor_callback, 0)
    return monitors


def selected_monitor(device: object, *, fallback_to_primary: bool = True) -> dict[str, object] | None:
    """Find a device; callers can explicitly handle a missing pin."""
    monitors = list_monitors()
    for monitor in monitors:
        if monitor["device"] == device:
            return monitor
    return primary_monitor(monitors) if fallback_to_primary else None


def primary_monitor(monitors: list[dict[str, object]] | None = None) -> dict[str, object] | None:
    """Return the primary work area without assuming its origin."""
    monitors = list_monitors() if monitors is None else monitors
    return next((monitor for monitor in monitors if monitor["primary"]), None)


def rectangle_visible(x: int, y: int, width: int, height: int,
                      monitors: list[dict[str, object]] | None = None) -> bool:
    """Require a usable 50 by 30 pixel intersection with one work area.

    For widgets smaller than the threshold, require their full dimension.
    """
    if width <= 0 or height <= 0:
        return False
    monitors = list_monitors() if monitors is None else monitors
    for monitor in monitors:
        overlap_x = min(x + width, int(monitor["right"])) - max(x, int(monitor["left"]))
        overlap_y = min(y + height, int(monitor["bottom"])) - max(y, int(monitor["top"]))
        if overlap_x >= min(50, width) and overlap_y >= min(30, height):
            return True
    return False


def safe_position(monitor: dict[str, object], width: int, height: int) -> tuple[int, int]:
    """Place near the work area's upper right, clamping oversized widgets."""
    left, top = int(monitor["left"]), int(monitor["top"])
    right, bottom = int(monitor["right"]), int(monitor["bottom"])
    return max(left, right - width - 22), max(top, min(top + 22, bottom - height))
