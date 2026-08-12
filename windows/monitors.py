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


def selected_monitor(device: object) -> dict[str, object] | None:
    monitors = list_monitors()
    for monitor in monitors:
        if monitor["device"] == device:
            return monitor
    return next((monitor for monitor in monitors if monitor["primary"]), None)
