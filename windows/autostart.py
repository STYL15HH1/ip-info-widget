"""Current-user Windows startup registry integration."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


APP_NAME = "IP Info Widget"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def autostart_command() -> str:
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([sys.executable])
    return subprocess.list2cmdline([sys.executable, str(Path(__file__).resolve().parents[1] / "app.py")])


def set_autostart(enabled: bool) -> None:
    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, autostart_command())
            try:
                winreg.DeleteValue(key, "My IP Widget")
            except FileNotFoundError:
                pass
        else:
            for value_name in (APP_NAME, "My IP Widget"):
                try:
                    winreg.DeleteValue(key, value_name)
                except FileNotFoundError:
                    pass
