"""Main Tkinter widget controller.

Network and Windows services return data/callbacks to this controller; they never
manipulate Tkinter widgets directly.  This keeps all Tk access on its main thread.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

from core.ip_monitor import IPMonitor
from core.models import PingResult, RefreshResult
from core.settings import SettingsManager
from core.storage import AppPaths
from core.version import APP_VERSION
from ui.about_window import AboutWindow
from ui.history_window import open_history_window
from ui.layouts import DisplayData, Theme, WidgetLayout, create_layout
from ui.menu import build_context_menu
from ui.settings_window import open_settings_window
from windows.autostart import set_autostart
from windows.monitors import list_monitors, primary_monitor, rectangle_visible, safe_position, selected_monitor
from windows.notifications import send_ip_change_notification
from windows.taskbar import TaskbarIcon
from windows.tray import TrayController


APP_NAME = "IP Info Widget"
THEMES = {
    "dark": Theme(background="#101419", foreground="#d3dbe5", muted="#8999ad", border="#303945"),
    "light": Theme(background="#f6f8fb", foreground="#1d2632", muted="#596879", border="#c6d0dc"),
}


class IPInfoWidget:
    def __init__(self, paths: AppPaths, settings: SettingsManager, monitor: IPMonitor) -> None:
        self.paths = paths
        self.settings = settings
        self.monitor = monitor
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", bool(self.settings.data["always_on_top"]))
        self.root.attributes("-alpha", float(self.settings.data["opacity"]))
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.bind("<Button-3>", self.show_menu)
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)
        self.root.bind("<ButtonRelease-1>", self.finish_drag)
        try:
            self.root.iconbitmap(default=str(self.paths.app_icon_path))
        except tk.TclError:
            pass

        self.root.update_idletasks()
        self.taskbar = TaskbarIcon(self.root)
        self.app_icon_image = self._load_app_icon()
        if self.app_icon_image is not None:
            self.taskbar.set_image("app", self.app_icon_image)

        self.card = tk.Frame(self.root, padx=14, pady=13)
        self.card.pack()
        self.layout: WidgetLayout | None = None
        self.display_data = DisplayData(country="Loading…", ip="Retrieving public IP…", flag_text="IP")
        self.flag_photo: ImageTk.PhotoImage | None = None
        self.current_country_flag: Image.Image | None = None
        self._drag_offset: tuple[int, int] | None = None
        self._queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._refresh_in_progress = False
        self._closed = False
        self._after_refresh: str | None = None
        self._last_result: RefreshResult | None = None
        self._about_window: AboutWindow | None = None
        self.context_menu = build_context_menu(
            self.root, self.refresh_now, self.test_connection_now, self.hide,
            self.show_history, self.open_settings, self.open_about, self.quit,
        )
        self.tray = TrayController(
            APP_NAME, self.paths.app_icon_path,
            lambda: self._queue.put(("show", None)),
            lambda: self._queue.put(("hide", None)),
            lambda: self._queue.put(("refresh", None)),
            lambda: self._queue.put(("quit", None)),
            lambda: self._queue.put(("restore_primary", None)),
        )
        self.rebuild_layout()
        self.restore_position()

    def run(self) -> None:
        self.tray.start()
        self.refresh_now()
        self.root.after(100, self.process_queue)
        self.root.mainloop()

    def rebuild_layout(self) -> None:
        had_layout = self.layout is not None
        x, y = self.root.winfo_x(), self.root.winfo_y()
        for child in self.card.winfo_children():
            child.destroy()
        self.layout = create_layout(str(self.settings.data["display_mode"]), self.card)
        self.layout.apply_theme(self.theme)
        self.card.configure(bg=self.theme.background)
        ip_label = getattr(self.layout, "ip", None)
        if ip_label is not None:
            ip_label.bind("<Button-1>", self.copy_ip)
        self.render(
            self.display_data,
            country_code=self.display_data.country_code.lower() or None,
            update_taskbar=False,
        )
        self.root.update_idletasks()
        if had_layout:
            self._validate_position(x, y)

    @property
    def theme(self) -> Theme:
        return THEMES.get(str(self.settings.data.get("theme")), THEMES["dark"])

    def _widget_size(self) -> tuple[int, int]:
        self.root.update_idletasks()
        return self.root.winfo_width(), self.root.winfo_height()

    def _place_position(self, x: int, y: int, save: bool = False) -> None:
        # A leading + with a signed value denotes an absolute virtual-desktop
        # coordinate in Tk; a bare - offset would anchor to the screen edge.
        self.root.geometry(f"+{x}+{y}")
        if save:
            self.settings.data.update({"x": x, "y": y})
            self.settings.save()

    def _validate_position(self, x: int, y: int) -> None:
        width, height = self._widget_size()
        monitors = list_monitors()
        if rectangle_visible(x, y, width, height, monitors):
            self._place_position(x, y)
            return
        primary = primary_monitor(monitors)
        if primary is not None:
            self._place_position(*safe_position(primary, width, height), save=True)
        else:
            # Enumeration failure is not evidence that saved coordinates are
            # invalid. Preserve them rather than persisting a guessed origin.
            self._place_position(x, y)

    def restore_position(self) -> None:
        x, y = self.settings.data.get("x"), self.settings.data.get("y")
        if self.settings.data.get("monitor_device"):
            self.move_to_selected_monitor()
        elif isinstance(x, int) and isinstance(y, int):
            self._validate_position(x, y)
        else:
            primary = primary_monitor()
            if primary is not None:
                self._place_position(*safe_position(primary, *self._widget_size()), save=True)

    def restore_to_primary_monitor(self) -> None:
        primary = primary_monitor()
        self.root.deiconify()
        width, height = self._widget_size()
        if primary is not None:
            self.settings.data["monitor_device"] = None
            self._place_position(*safe_position(primary, width, height), save=True)
        self.root.attributes("-topmost", bool(self.settings.data["always_on_top"]))
        self.root.lift()

    def move_to_selected_monitor(self) -> None:
        monitor = selected_monitor(self.settings.data.get("monitor_device"), fallback_to_primary=False)
        missing = monitor is None
        if missing:
            # Keep the configured pin so it works again when the display returns.
            monitor = primary_monitor()
        if monitor is not None:
            width, height = self._widget_size()
            self._place_position(*safe_position(monitor, width, height), save=missing)

    def start_drag(self, event: tk.Event) -> None:
        self._drag_offset = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def drag(self, event: tk.Event) -> None:
        if self._drag_offset is None:
            return
        x, y = event.x_root - self._drag_offset[0], event.y_root - self._drag_offset[1]
        if self.settings.data.get("monitor_device"):
            monitor = selected_monitor(self.settings.data.get("monitor_device"))
            if monitor:
                self.root.update_idletasks()
                x = max(int(monitor["left"]), min(x, int(monitor["right"]) - self.root.winfo_width()))
                y = max(int(monitor["top"]), min(y, int(monitor["bottom"]) - self.root.winfo_height()))
        self.root.geometry(f"+{x}+{y}")

    def finish_drag(self, _event: tk.Event | None = None) -> None:
        self._drag_offset = None
        self.settings.update({"x": self.root.winfo_x(), "y": self.root.winfo_y()})
        self.settings.save()

    def show_menu(self, event: tk.Event) -> None:
        self.context_menu.tk_popup(event.x_root, event.y_root)
        self.context_menu.grab_release()

    def copy_ip(self, _event: tk.Event | None = None) -> str:
        if not self.display_data.ip or self.display_data.ip.startswith("Could not"):
            return "break"
        self.root.clipboard_clear()
        self.root.clipboard_append(self.display_data.ip)
        self.root.update_idletasks()
        return "break"

    def refresh_now(self) -> None:
        self._start_refresh(force_ping=False)

    def test_connection_now(self) -> None:
        self._start_refresh(force_ping=True)

    def _start_refresh(self, force_ping: bool) -> None:
        if self._refresh_in_progress or self._closed:
            return
        self._refresh_in_progress = True
        run_ping = force_ping or bool(self.settings.data.get("ping_enabled"))
        thread = threading.Thread(
            target=self._refresh_worker,
            args=(str(self.settings.data.get("ping_host", "1.1.1.1")), run_ping), daemon=True,
        )
        thread.start()

    def _refresh_worker(self, ping_host: str, run_ping: bool) -> None:
        try:
            self._queue.put(("result", self.monitor.refresh(ping_host, run_ping)))
        except Exception as error:  # UI turns service errors into a stable visible message.
            self._queue.put(("error", error))

    def process_queue(self) -> None:
        if self._closed:
            return
        try:
            while True:
                action, payload = self._queue.get_nowait()
                if action == "result":
                    self._refresh_in_progress = False
                    self.handle_result(payload)  # type: ignore[arg-type]
                elif action == "error":
                    self._refresh_in_progress = False
                    self.render_error()
                elif action == "show":
                    self.show()
                elif action == "hide":
                    self.hide()
                elif action == "refresh":
                    self.refresh_now()
                elif action == "restore_primary":
                    self.restore_to_primary_monitor()
                elif action == "quit":
                    self.quit()
        except queue.Empty:
            pass
        if not self._closed:
            self.root.after(100, self.process_queue)

    def handle_result(self, result: RefreshResult) -> None:
        self._last_result = result
        info = result.info
        ping_text = self._ping_text(result.ping)
        self.render(DisplayData(
            country=info.country, country_code=info.country_code.upper(), ip=info.ip,
            city=info.city if self.settings.data.get("show_location") else "",
            isp=info.isp if self.settings.data.get("show_isp") else "",
            ping_text=ping_text, flag_text=info.country_code.upper(),
        ), country_code=info.country_code)
        self.tray.set_ip(info.ip, self.current_country_flag)
        if result.change is not None:
            send_ip_change_notification(APP_NAME, result.change)
        self.schedule_next_refresh()

    @staticmethod
    def _ping_text(ping: PingResult | None) -> str:
        if ping is None:
            return ""
        if ping.reachable:
            return f"Ping: {ping.latency_ms} ms" if ping.latency_ms is not None else "Ping: reachable"
        return f"Ping: {ping.host} unavailable"

    def render_error(self) -> None:
        # Retain the last country taskbar icon after an API failure.
        self.render(DisplayData(country="No connection", ip="Could not retrieve IP", city="Right-click to refresh", flag_text="IP"), update_taskbar=False)
        self.schedule_next_refresh()

    def render(self, data: DisplayData, country_code: str | None = None, update_taskbar: bool = True) -> None:
        self.display_data = data
        flag = self.load_flag(country_code) if country_code else None
        if flag is not None:
            self.current_country_flag = flag
            preview_size = (30, 22) if self.settings.data.get("display_mode") == "compact" else (52, 39)
            preview = flag.copy()
            preview.thumbnail(preview_size, Image.Resampling.LANCZOS)
            self.flag_photo = ImageTk.PhotoImage(preview)
            data.flag_image = self.flag_photo
            # Tk's native window icon is a separate fallback path used by some
            # Explorer taskbar configurations; retain the PhotoImage reference.
            self.root.iconphoto(False, self.flag_photo)
            if update_taskbar and country_code:
                self.taskbar.set_image(f"country:{country_code.lower()}", flag)
        elif country_code and update_taskbar and self.app_icon_image is not None:
            self.current_country_flag = None
            # Missing local flag: use the normal application icon instead.
            self.taskbar.set_image("app", self.app_icon_image)
        if self.layout is not None:
            self.layout.render(data)
            self.layout.apply_theme(self.theme)

    def load_flag(self, country_code: str | None) -> Image.Image | None:
        if not country_code:
            return None
        path = self.paths.flags_dir / f"{country_code.lower()}.png"
        try:
            with Image.open(path) as source:
                return source.convert("RGBA")
        except (OSError, ValueError):
            return None

    def _load_app_icon(self) -> Image.Image | None:
        try:
            with Image.open(self.paths.app_icon_path) as source:
                return source.convert("RGBA")
        except (OSError, ValueError):
            image = Image.new("RGBA", (64, 64), "#1976d2")
            draw = ImageDraw.Draw(image)
            draw.text((18, 22), "IP", fill="white")
            return image

    def schedule_next_refresh(self) -> None:
        if self._after_refresh is not None:
            self.root.after_cancel(self._after_refresh)
        delay = int(self.settings.data.get("refresh_seconds", 5)) * 1000
        self._after_refresh = self.root.after(delay, self.refresh_now)

    def open_settings(self) -> None:
        open_settings_window(self.root, self.settings.data, list_monitors(), self.paths.portable, self.save_settings)

    def save_settings(self, values: dict[str, object]) -> None:
        previous_mode = self.settings.data.get("display_mode")
        previous_monitor = self.settings.data.get("monitor_device")
        if self.paths.portable:
            values["autostart"] = False
        else:
            set_autostart(bool(values.get("autostart")))
        self.settings.update(values)
        self.settings.save()
        self.root.attributes("-topmost", bool(self.settings.data["always_on_top"]))
        self.root.attributes("-alpha", float(self.settings.data["opacity"]))
        if previous_mode != self.settings.data.get("display_mode"):
            self.rebuild_layout()
        else:
            self.render(self.display_data, update_taskbar=False)
        if previous_monitor != self.settings.data.get("monitor_device"):
            self.move_to_selected_monitor()
        self.schedule_next_refresh()
        self.refresh_now()

    def show_history(self) -> None:
        open_history_window(self.root, self.monitor.history)

    def open_about(self) -> None:
        if self._about_window is not None and self._about_window.dialog.winfo_exists():
            self._about_window.focus()
            return
        self._about_window = AboutWindow(
            self.root, APP_VERSION, self.theme, self.paths.app_icon_path,
            self.paths.author_image_path, lambda: setattr(self, "_about_window", None),
        )

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()

    def hide(self) -> None:
        self.root.withdraw()

    def quit(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._after_refresh is not None:
            self.root.after_cancel(self._after_refresh)
        self.finish_drag()
        self.tray.stop()
        self.taskbar.clear()
        self.root.destroy()
