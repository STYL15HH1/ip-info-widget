"""Widget context-menu construction."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable


def build_context_menu(root: tk.Tk, refresh: Callable[[], None], test_connection: Callable[[], None], hide: Callable[[], None], history: Callable[[], None], settings: Callable[[], None], about: Callable[[], None], quit_app: Callable[[], None]) -> tk.Menu:
    menu = tk.Menu(root, tearoff=False)
    menu.add_command(label="Refresh now", command=refresh)
    menu.add_command(label="Test connection now", command=test_connection)
    menu.add_command(label="Hide widget", command=hide)
    menu.add_command(label="IP change history", command=history)
    menu.add_command(label="Settings", command=settings)
    menu.add_separator()
    menu.add_command(label="About", command=about)
    menu.add_command(label="Quit", command=quit_app)
    return menu
