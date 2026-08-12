"""Small themed About dialog for IP Info Widget."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageTk

from ui.layouts import Theme


APP_NAME = "IP Info Widget"
AUTHOR_NAME = "STYL15HH1"
REPOSITORY_URL = "https://github.com/STYL15HH1/ip-info-widget"


class AboutWindow:
    """A single themed dialog instance, owned by the main widget controller."""

    def __init__(
        self,
        parent: tk.Tk,
        version: str,
        theme: Theme,
        icon_path: Path,
        author_image_path: Path,
        on_closed: Callable[[], None],
    ) -> None:
        self.parent = parent
        self._on_closed = on_closed
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"About - {APP_NAME}")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.protocol("WM_DELETE_WINDOW", self.close)
        try:
            self.dialog.iconbitmap(default=str(icon_path))
        except tk.TclError:
            pass

        self._build(version, theme, author_image_path)
        self._center_on_parent()
        self.dialog.grab_set()

    def focus(self) -> None:
        self.dialog.deiconify()
        self.dialog.lift()
        self.dialog.focus_force()

    def close(self) -> None:
        if self.dialog.winfo_exists():
            self.dialog.destroy()
        self._on_closed()

    def _build(self, version: str, theme: Theme, author_image_path: Path) -> None:
        dialog = self.dialog
        dialog.configure(bg=theme.background)
        content = tk.Frame(dialog, bg=theme.background, padx=24, pady=20)
        content.pack(fill="both", expand=True)

        tk.Label(content, text=APP_NAME, font=("Segoe UI Semibold", 16), bg=theme.background, fg=theme.foreground).pack()
        tk.Label(content, text=f"Version {version}", font=("Segoe UI", 9), bg=theme.background, fg=theme.muted).pack(pady=(2, 12))
        tk.Label(
            content,
            text="A lightweight Windows widget for monitoring your public IP\naddress, network location and IP changes in real time.",
            justify="center", font=("Segoe UI", 9), bg=theme.background, fg=theme.foreground,
        ).pack()

        tk.Frame(content, height=1, bg=theme.border).pack(fill="x", pady=16)
        tk.Label(content, text="Created by", font=("Segoe UI", 8), bg=theme.background, fg=theme.muted).pack(anchor="w")
        author_row = tk.Frame(content, bg=theme.background)
        author_row.pack(fill="x", pady=(6, 12))
        self.author_photo = self._load_author_photo(author_image_path)
        if self.author_photo is not None:
            tk.Label(author_row, image=self.author_photo, bg=theme.background).pack(side="left", padx=(0, 11))
        author_text = tk.Frame(author_row, bg=theme.background)
        author_text.pack(side="left", anchor="w")
        name = tk.Label(author_text, text=AUTHOR_NAME, font=("Segoe UI Semibold", 11), bg=theme.background, fg="#1fa7ca", cursor="hand2")
        name.pack(anchor="w")
        name.bind("<Button-1>", self._open_repository)
        tk.Label(author_text, text="GitHub Developer", font=("Segoe UI", 8), bg=theme.background, fg=theme.muted).pack(anchor="w")

        repository = tk.Label(
            content, text="GitHub: github.com/STYL15HH1/ip-info-widget", font=("Segoe UI", 8),
            bg=theme.background, fg="#1fa7ca", cursor="hand2",
        )
        repository.pack(anchor="w")
        repository.bind("<Button-1>", self._open_repository)
        tk.Frame(content, height=1, bg=theme.border).pack(fill="x", pady=16)
        tk.Label(content, text="MIT License\n© 2026 STYL15HH1", justify="center", font=("Segoe UI", 8), bg=theme.background, fg=theme.muted).pack()
        tk.Button(
            content, text="Close", command=self.close, width=11, font=("Segoe UI", 9),
            bg=theme.background, fg=theme.foreground, activebackground=theme.border,
            activeforeground=theme.foreground, highlightbackground=theme.border,
        ).pack(pady=(16, 0))

    @staticmethod
    def _load_author_photo(path: Path) -> ImageTk.PhotoImage | None:
        try:
            with Image.open(path) as source:
                image = source.convert("RGBA")
            image.thumbnail((64, 64), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        except (OSError, ValueError):
            return None

    def _center_on_parent(self) -> None:
        self.parent.update_idletasks()
        self.dialog.update_idletasks()
        width, height = self.dialog.winfo_reqwidth(), self.dialog.winfo_reqheight()
        x = self.parent.winfo_rootx() + max(0, (self.parent.winfo_width() - width) // 2)
        y = self.parent.winfo_rooty() + max(0, (self.parent.winfo_height() - height) // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def _open_repository(_event: tk.Event | None = None) -> None:
        webbrowser.open_new_tab(REPOSITORY_URL)
