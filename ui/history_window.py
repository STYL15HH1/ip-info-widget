"""IP history Tkinter dialog."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from core.history import HistoryStore


def open_history_window(parent: tk.Tk, history: HistoryStore) -> None:
    dialog = tk.Toplevel(parent)
    dialog.title("IP change history")
    dialog.geometry("710x310")
    dialog.minsize(560, 220)
    dialog.transient(parent)
    columns = ("time", "old", "new", "country")
    table = ttk.Treeview(dialog, columns=columns, show="headings")
    headings = {"time": "Changed at", "old": "Previous IP", "new": "New IP", "country": "Country"}
    widths = {"time": 170, "old": 145, "new": 145, "country": 190}
    for column in columns:
        table.heading(column, text=headings[column])
        table.column(column, width=widths[column], anchor="w")
    for entry in reversed(history.load()):
        table.insert("", "end", values=(
            history.display_time(entry), entry.get("old_ip", ""), entry.get("new_ip", ""), entry.get("country", ""),
        ))
    table.pack(fill="both", expand=True, padx=12, pady=(12, 6))

    def clear() -> None:
        history.clear()
        for item in table.get_children():
            table.delete(item)

    ttk.Button(dialog, text="Clear history", command=clear).pack(anchor="e", padx=12, pady=(0, 10))
