"""Settings dialog, intentionally isolated from the widget lifecycle."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from core.settings import DISPLAY_MODES


def open_settings_window(parent: tk.Tk, settings: dict[str, object], monitors: list[dict[str, object]], portable: bool, save: Callable[[dict[str, object]], None]) -> None:
    dialog = tk.Toplevel(parent)
    dialog.title("Settings — IP Info Widget")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.configure(padx=18, pady=15)

    display_mode = tk.StringVar(value=str(settings.get("display_mode", "normal")).title())
    theme = tk.StringVar(value=str(settings.get("theme", "dark")).title())
    refresh = tk.IntVar(value=int(settings.get("refresh_seconds", 5)))
    opacity = tk.IntVar(value=round(float(settings.get("opacity", 0.92)) * 100))
    show_location = tk.BooleanVar(value=bool(settings.get("show_location", True)))
    show_isp = tk.BooleanVar(value=bool(settings.get("show_isp", False)))
    ping_host = tk.StringVar(value=str(settings.get("ping_host", "1.1.1.1")))
    ping_enabled = tk.BooleanVar(value=bool(settings.get("ping_enabled", False)))
    autostart = tk.BooleanVar(value=bool(settings.get("autostart", False)) and not portable)
    always_on_top = tk.BooleanVar(value=bool(settings.get("always_on_top", True)))
    any_monitor = "Any monitor"
    monitor_options = [any_monitor] + [str(item["label"]) for item in monitors]
    device_by_label = {str(item["label"]): item["device"] for item in monitors}
    selected_label = next((str(item["label"]) for item in monitors if item["device"] == settings.get("monitor_device")), any_monitor)
    monitor_choice = tk.StringVar(value=selected_label)

    ttk.Label(dialog, text="Display mode:").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Combobox(dialog, textvariable=display_mode, values=tuple(mode.title() for mode in DISPLAY_MODES), state="readonly", width=18).grid(row=0, column=1, sticky="ew", pady=4)
    ttk.Label(dialog, text="Theme:").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Combobox(dialog, textvariable=theme, values=("Dark", "Light"), state="readonly", width=18).grid(row=1, column=1, sticky="ew", pady=4)
    ttk.Label(dialog, text="Refresh interval (sec):").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Spinbox(dialog, from_=5, to=86400, textvariable=refresh, width=20).grid(row=2, column=1, sticky="ew", pady=4)
    ttk.Label(dialog, text="Opacity:").grid(row=3, column=0, sticky="w", pady=4)
    ttk.Scale(dialog, from_=55, to=100, variable=opacity, orient="horizontal").grid(row=3, column=1, sticky="ew", pady=4)
    ttk.Checkbutton(dialog, text="Show city", variable=show_location).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 2))
    ttk.Checkbutton(dialog, text="Show internet provider", variable=show_isp).grid(row=5, column=0, columnspan=2, sticky="w", pady=2)
    ttk.Label(dialog, text="Pin to monitor:").grid(row=6, column=0, sticky="w", pady=(8, 4))
    ttk.Combobox(dialog, textvariable=monitor_choice, values=monitor_options, state="readonly", width=28).grid(row=6, column=1, sticky="ew", pady=(8, 4))
    ttk.Label(dialog, text="Ping host:").grid(row=7, column=0, sticky="w", pady=(4, 4))
    ttk.Entry(dialog, textvariable=ping_host, width=30).grid(row=7, column=1, sticky="ew", pady=(4, 4))
    ttk.Checkbutton(dialog, text="Test ping on every refresh", variable=ping_enabled).grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 2))
    autostart_check = ttk.Checkbutton(dialog, text="Start widget with Windows", variable=autostart)
    autostart_check.grid(row=9, column=0, columnspan=2, sticky="w", pady=2)
    if portable:
        autostart_check.configure(state="disabled")
        ttk.Label(dialog, text="Autostart is disabled in Portable Mode.").grid(row=10, column=0, columnspan=2, sticky="w", pady=(0, 2))
        topmost_row = 11
    else:
        topmost_row = 10
    ttk.Checkbutton(dialog, text="Always on top of other apps", variable=always_on_top).grid(row=topmost_row, column=0, columnspan=2, sticky="w", pady=2)

    def apply() -> None:
        try:
            refresh_value = max(5, refresh.get())
        except tk.TclError:
            messagebox.showerror("Invalid value", "Refresh interval must be a whole number (at least 5 seconds).", parent=dialog)
            return
        values: dict[str, object] = {
            "display_mode": display_mode.get().lower(),
            "theme": theme.get().lower(),
            "refresh_seconds": refresh_value,
            "opacity": max(0.55, min(1, opacity.get() / 100)),
            "show_location": show_location.get(),
            "show_isp": show_isp.get(),
            "monitor_device": device_by_label.get(monitor_choice.get()),
            "ping_host": ping_host.get().strip() or "1.1.1.1",
            "ping_enabled": ping_enabled.get(),
            "autostart": False if portable else autostart.get(),
            "always_on_top": always_on_top.get(),
        }
        try:
            save(values)
        except OSError as error:
            messagebox.showerror("Could not save settings", str(error), parent=dialog)
            return
        dialog.destroy()

    ttk.Button(dialog, text="Save", command=apply).grid(row=topmost_row + 1, column=0, columnspan=2, pady=(13, 0))
