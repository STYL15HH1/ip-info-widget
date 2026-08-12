"""Independent widget layouts sharing one display-data model."""

from __future__ import annotations

from dataclasses import dataclass

import tkinter as tk


@dataclass
class DisplayData:
    country: str = ""
    country_code: str = ""
    ip: str = ""
    city: str = ""
    isp: str = ""
    ping_text: str = ""
    flag_image: object | None = None
    flag_text: str = ""


@dataclass
class Theme:
    background: str
    foreground: str
    muted: str
    border: str


class WidgetLayout:
    def __init__(self, parent: tk.Widget) -> None:
        self.parent = parent
        self.labels: list[tuple[tk.Label, str]] = []

    def label(self, font, role: str = "foreground", cursor: str = "fleur") -> tk.Label:
        item = tk.Label(self.parent, font=font, cursor=cursor)
        self.labels.append((item, role))
        return item

    def apply_theme(self, theme: Theme) -> None:
        self.parent.configure(bg=theme.background, highlightbackground=theme.border, highlightthickness=1)
        for label, role in self.labels:
            label.configure(bg=theme.background, fg=getattr(theme, role))

    def render(self, data: DisplayData) -> None:
        raise NotImplementedError


class CompactLayout(WidgetLayout):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.flag = self.label(("Segoe UI Emoji", 13), cursor="fleur")
        self.ip = self.label(("Cascadia Mono", 11, "bold"), cursor="hand2")
        self.flag.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.ip.grid(row=0, column=1, sticky="w")

    def render(self, data: DisplayData) -> None:
        self.flag.configure(image=data.flag_image or "", text="" if data.flag_image else data.flag_text)
        self.ip.configure(text=data.ip)


class NormalLayout(WidgetLayout):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.country = self.label(("Segoe UI Semibold", 10))
        self.code = self.label(("Cascadia Mono", 16, "bold"))
        self.ip = self.label(("Cascadia Mono", 11, "bold"), cursor="hand2")
        self.flag = self.label(("Segoe UI Emoji", 16))
        self.details = self.label(("Segoe UI", 8), "muted")
        self.country.grid(row=0, column=1, sticky="w")
        self.code.grid(row=1, column=0, padx=(0, 10), sticky="sw")
        self.ip.grid(row=1, column=1, sticky="w", pady=(2, 0))
        self.flag.grid(row=2, column=0, padx=(0, 10), sticky="sw")
        self.details.grid(row=2, column=1, sticky="w", pady=(5, 0))

    def render(self, data: DisplayData) -> None:
        self.country.configure(text=data.country)
        self.code.configure(text=data.country_code)
        self.ip.configure(text=data.ip)
        self.flag.configure(image=data.flag_image or "", text="" if data.flag_image else data.flag_text)
        self.details.configure(text=" • ".join(part for part in (data.city, data.isp) if part))


class MonitoringLayout(WidgetLayout):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.country = self.label(("Segoe UI Semibold", 10))
        self.code = self.label(("Cascadia Mono", 16, "bold"))
        self.ip = self.label(("Cascadia Mono", 11, "bold"), cursor="hand2")
        self.flag = self.label(("Segoe UI Emoji", 16))
        self.city = self.label(("Segoe UI", 8), "muted")
        self.isp = self.label(("Segoe UI", 8), "muted")
        self.ping = self.label(("Segoe UI", 8), "muted")
        self.country.grid(row=0, column=1, sticky="w")
        self.code.grid(row=1, column=0, padx=(0, 10), sticky="sw")
        self.ip.grid(row=1, column=1, sticky="w", pady=(2, 0))
        self.flag.grid(row=2, column=0, rowspan=3, padx=(0, 10), sticky="sw")
        self.city.grid(row=2, column=1, sticky="w", pady=(5, 0))
        self.isp.grid(row=3, column=1, sticky="w")
        self.ping.grid(row=4, column=1, sticky="w")

    def render(self, data: DisplayData) -> None:
        self.country.configure(text=data.country)
        self.code.configure(text=data.country_code)
        self.ip.configure(text=data.ip)
        self.flag.configure(image=data.flag_image or "", text="" if data.flag_image else data.flag_text)
        self.city.configure(text=f"City: {data.city or 'not available'}")
        self.isp.configure(text=f"ISP: {data.isp or 'not available'}")
        self.ping.configure(text=data.ping_text or "Ping: not tested")


def create_layout(mode: str, parent: tk.Widget) -> WidgetLayout:
    if mode == "compact":
        return CompactLayout(parent)
    if mode == "monitoring":
        return MonitoringLayout(parent)
    return NormalLayout(parent)
