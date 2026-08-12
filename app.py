"""IP Info Widget application entry point.

Run normally with ``python app.py`` or with self-contained configuration using
``python app.py --portable``.  The Tk/PyInstaller setup stays here because it
must execute before any Tkinter imports.
"""

from __future__ import annotations

import os
import sys


# PyInstaller can miss Tcl/Tk resource discovery in some Windows environments.
# Point Tk at the bundled directories before importing the UI layer.
if getattr(sys, "frozen", False):
    bundle_root = str(getattr(sys, "_MEIPASS", ""))
    os.environ["TCL_LIBRARY"] = os.path.join(bundle_root, "_tcl_data")
    os.environ["TK_LIBRARY"] = os.path.join(bundle_root, "_tk_data")

from core.history import HistoryStore
from core.ip_monitor import IPMonitor
from core.ip_service import IPService
from core.settings import SettingsManager
from core.storage import AppPaths, portable_requested
from windows.taskbar import set_process_app_user_model_id
from ui.widget import IPInfoWidget


def main() -> None:
    set_process_app_user_model_id()
    paths = AppPaths(portable_requested())
    paths.ensure_data_directories()
    settings = SettingsManager(paths)
    # A removable drive letter is not stable, so no portable run may retain a
    # Windows autostart preference.
    if paths.portable:
        settings.update({"autostart": False})
    history = HistoryStore(paths)
    monitor = IPMonitor(IPService(), history)
    IPInfoWidget(paths, settings, monitor).run()


if __name__ == "__main__":
    main()
