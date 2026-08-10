"""My IP Widget — lekki widżet informacji o połączeniu dla Windows.

Uruchom: python app.py
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
import ctypes
from ctypes import wintypes
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# PyInstaller nie rozpoznaje automatycznie Tcl/Tk w niektórych środowiskach.
# W gotowym EXE wskazujemy dołączone biblioteki zanim zaimportujemy tkinter.
if getattr(sys, "frozen", False):
    bundle_root = getattr(sys, "_MEIPASS", "")
    # PyInstaller uruchamia Tcl/Tk z katalogów o tych nazwach. Ich użycie
    # pozwala również skryptowi startowemu PyInstallera ustawić je poprawnie.
    os.environ["TCL_LIBRARY"] = os.path.join(bundle_root, "_tcl_data")
    os.environ["TK_LIBRARY"] = os.path.join(bundle_root, "_tk_data")

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageTk

try:
    import pystray
except ImportError:  # Widżet nadal działa, lecz bez ikony w trayu.
    pystray = None

try:
    from winotify import Notification, audio
except ImportError:  # Powiadomienia wymagają pakietu winotify.
    Notification = None


APP_NAME = "IP Info Widget"
SETTINGS_PATH = Path.home() / "AppData" / "Local" / "MyIPWidget" / "settings.json"
HISTORY_PATH = SETTINGS_PATH.parent / "ip-history.json"
FLAGS_DIR = Path(__file__).parent / "assets" / "images" / "flags"
APP_ICON_PATH = Path(__file__).parent / "assets" / "icons" / "ip-info-widget.ico"
DEFAULTS = {
    "theme": "dark",
    "opacity": 0.92,
    # Tak jak w oryginalnym widżecie: szybkie wykrycie przełączenia VPN/IP.
    "refresh_seconds": 5,
    "show_location": True,
    "show_isp": False,
    "monitor_device": None,
    "ping_host": "1.1.1.1",
    "ping_enabled": False,
    "autostart": False,
    "always_on_top": True,
    "x": None,
    "y": None,
}

TRANSLATIONS = {
    "pl": {
        "connecting": "Łączenie…", "updating": "Aktualizowanie…", "refresh": "Odśwież teraz",
        "ping_now": "Test połączenia teraz", "hide_widget": "Ukryj widget", "show_widget": "Pokaż widget",
        "history": "Historia zmian IP", "settings": "Ustawienia", "quit": "Zamknij",
        "unknown_ip": "Nieznane IP", "copied_ip": "Skopiowano IP", "no_connection": "Brak połączenia",
        "fetch_failed": "Nie udało się pobrać IP", "retry_hint": "Kliknij prawym przyciskiem → Odśwież",
        "connection_unavailable": "Internet: brak połączenia", "connection_ok": "Internet: OK",
        "no_response": "brak odpowiedzi", "ip_changed": "IP zmienione", "unknown_location": "Nieznana lokalizacja",
        "notification_title": "Zmieniono publiczne IP", "history_title": "Historia zmian IP",
        "time": "Czas zmiany", "previous_ip": "Poprzednie IP", "new_ip": "Nowe IP", "country": "Kraj",
        "clear_history": "Wyczyść historię", "settings_title": "Ustawienia — {app}",
        "language": "Język:", "system_language": "Systemowy (Windows: {language})", "polish": "Polski", "english": "English",
        "theme": "Motyw:", "dark": "Ciemny", "light": "Jasny", "refresh_seconds": "Odświeżanie (sek.):",
        "opacity": "Przezroczystość:", "show_city": "Pokazuj miasto", "show_isp": "Pokazuj dostawcę internetu",
        "pin_monitor": "Przypnij do monitora:", "any_monitor": "Dowolny monitor", "ping_host": "Host do pingowania:",
        "ping_refresh": "Testuj ping przy każdym odświeżeniu", "autostart": "Uruchamiaj widget wraz z Windowsem",
        "always_on_top": "Zawsze na wierzchu innych aplikacji", "save": "Zapisz", "invalid_value": "Nieprawidłowa wartość",
        "refresh_error": "Odświeżanie musi być liczbą całkowitą (co najmniej 5 sekund).",
        "autostart_error": "Nie udało się zmienić autostartu", "monitor": "Monitor {number}{primary} — {width}×{height}",
        "primary_monitor": " (główny)", "service_error": "Usługa nie zwróciła danych.",
    },
    "en": {
        "connecting": "Connecting…", "updating": "Updating…", "refresh": "Refresh now",
        "ping_now": "Test connection now", "hide_widget": "Hide widget", "show_widget": "Show widget",
        "history": "IP change history", "settings": "Settings", "quit": "Quit",
        "unknown_ip": "Unknown IP", "copied_ip": "IP copied", "no_connection": "No connection",
        "fetch_failed": "Could not retrieve IP", "retry_hint": "Right-click → Refresh",
        "connection_unavailable": "Internet: unavailable", "connection_ok": "Internet: OK",
        "no_response": "no response", "ip_changed": "IP changed", "unknown_location": "Unknown location",
        "notification_title": "Public IP changed", "history_title": "IP change history",
        "time": "Changed at", "previous_ip": "Previous IP", "new_ip": "New IP", "country": "Country",
        "clear_history": "Clear history", "settings_title": "Settings — {app}",
        "language": "Language:", "system_language": "System default (Windows: {language})", "polish": "Polish", "english": "English",
        "theme": "Theme:", "dark": "Dark", "light": "Light", "refresh_seconds": "Refresh interval (sec):",
        "opacity": "Opacity:", "show_city": "Show city", "show_isp": "Show internet provider",
        "pin_monitor": "Pin to monitor:", "any_monitor": "Any monitor", "ping_host": "Ping host:",
        "ping_refresh": "Test ping on every refresh", "autostart": "Start widget with Windows",
        "always_on_top": "Always on top of other apps", "save": "Save", "invalid_value": "Invalid value",
        "refresh_error": "Refresh interval must be a whole number (at least 5 seconds).",
        "autostart_error": "Could not change autostart", "monitor": "Monitor {number}{primary} — {width}×{height}",
        "primary_monitor": " (primary)", "service_error": "The service did not return data.",
    },
}


def detect_system_language() -> str:
    """Returns the UI language selected in Windows; English is the fallback."""
    try:
        language_code = locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "")
    except (AttributeError, OSError):
        language_code = locale.getlocale()[0] or ""
    return "pl" if language_code.lower().startswith("pl") else "en"


def resolve_language(value: str | None) -> str:
    return value if value in TRANSLATIONS else detect_system_language()


def tr(language: str, key: str, **values: object) -> str:
    return TRANSLATIONS[language][key].format(**values)


def load_settings() -> dict:
    try:
        values = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        return {**DEFAULTS, **values}
    except (OSError, json.JSONDecodeError):
        return DEFAULTS.copy()


def save_settings(values: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(values, indent=2), encoding="utf-8")


def load_history() -> list[dict]:
    try:
        entries = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return entries if isinstance(entries, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_history(entries: list[dict]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(entries[-50:], indent=2, ensure_ascii=False), encoding="utf-8")


def country_flag(country_code: str) -> str:
    """Zmienia kod ISO kraju, np. PL, na emoji flagi."""
    if len(country_code) != 2 or not country_code.isalpha():
        return "◎"
    return "".join(chr(0x1F1E6 + ord(letter) - ord("A")) for letter in country_code.upper())


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT), ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD), ("szDevice", ctypes.c_wchar * 32)]


def list_monitors(language: str) -> list[dict]:
    """Zwraca obszary wszystkich monitorów Windows wirtualnego pulpitu."""
    if not hasattr(ctypes, "windll"):
        return []
    monitors: list[dict] = []
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HANDLE, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM,
    )

    def callback(handle, _hdc, _rect, _data):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(info)
        if user32.GetMonitorInfoW(handle, ctypes.byref(info)):
            number = len(monitors) + 1
            width = info.rcWork.right - info.rcWork.left
            height = info.rcWork.bottom - info.rcWork.top
            primary = tr(language, "primary_monitor") if info.dwFlags & 1 else ""
            monitors.append({
                "device": info.szDevice,
                "label": tr(language, "monitor", number=number, primary=primary, width=width, height=height),
                "left": info.rcWork.left, "top": info.rcWork.top,
                "right": info.rcWork.right, "bottom": info.rcWork.bottom,
                "primary": bool(info.dwFlags & 1),
            })
        return True

    enum_callback = callback_type(callback)
    user32.EnumDisplayMonitors(None, None, enum_callback, 0)
    return monitors


def ping_host(host: str) -> dict:
    """Wykonuje pojedynczy ping Windows i zwraca czas odpowiedzi w ms."""
    host = host.strip()
    if not host:
        return {"reachable": False, "latency_ms": None}
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "1500", host],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        output = result.stdout + result.stderr
        # Obsługa wyników systemu Windows po polsku i po angielsku.
        match = re.search(r"(?:time|czas)\s*[=<]\s*(\d+)\s*ms", output, re.IGNORECASE)
        latency = int(match.group(1)) if match else (0 if result.returncode == 0 else None)
        return {"reachable": result.returncode == 0, "latency_ms": latency}
    except (OSError, subprocess.SubprocessError):
        return {"reachable": False, "latency_ms": None}


def autostart_command() -> str:
    """Buduje poprawnie cytowaną komendę dla wpisu Windows Run."""
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([sys.executable])
    return subprocess.list2cmdline([sys.executable, str(Path(__file__).resolve())])


def set_autostart(enabled: bool) -> None:
    """Dodaje albo usuwa autostart wyłącznie dla bieżącego użytkownika."""
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
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


class IPWidget:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.language = "en"
        self.inbox: queue.Queue[dict | Exception] = queue.Queue()
        self.actions: queue.Queue[Callable[[], None]] = queue.Queue()
        self.is_fetching = False
        self.closed = False
        self.tray = None
        self.drag_offset = (0, 0)
        self.current_ip: str | None = None
        self.copy_notice_id: str | None = None
        self.connection_status = self.t("connecting")

        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        try:
            self.root.iconbitmap(default=str(APP_ICON_PATH))
        except tk.TclError:
            pass
        self.apply_always_on_top()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)
        self.root.bind("<ButtonRelease-1>", self.finish_drag)
        self.root.bind("<Button-3>", self.open_menu)

        self.card = tk.Frame(self.root, padx=16, pady=13, cursor="fleur")
        self.card.pack(fill="both", expand=True)
        # Flagi PNG są tymi samymi plikami, których używa oryginalny My-IP-Widget.
        self.flag_image: ImageTk.PhotoImage | None = None
        self.flag = tk.Label(self.card, cursor="fleur")
        self.flag.grid(row=2, column=0, rowspan=2, padx=(0, 10), sticky="sw")
        self.country_code_label = tk.Label(self.card, font=("Cascadia Mono", 16, "bold"), cursor="fleur")
        self.country_code_label.grid(row=1, column=0, padx=(0, 10), sticky="sw")
        self.place_label = tk.Label(self.card, font=("Segoe UI Semibold", 10), cursor="fleur")
        self.place_label.grid(row=0, column=1, sticky="w")
        self.ip_label = tk.Label(self.card, font=("Cascadia Mono", 11, "bold"), cursor="hand2")
        self.ip_label.grid(row=1, column=1, sticky="w", pady=(2, 0))
        self.ip_label.bind("<Button-1>", self.copy_ip)
        self.detail_label = tk.Label(self.card, font=("Segoe UI", 8), cursor="fleur")
        self.detail_label.grid(row=2, column=1, sticky="w", pady=(5, 0))
        self.status = tk.Label(self.card, font=("Segoe UI", 8), cursor="fleur")
        # Status is kept internally for errors and clipboard feedback, but is
        # intentionally not shown to avoid distracting refresh-state flicker.

        self.build_menu()

        self.apply_theme()
        self.restore_position()
        self.create_tray()
        self.fetch()
        self.root.after(250, self.process_inbox)

    def t(self, key: str, **values: object) -> str:
        return tr(self.language, key, **values)

    def build_menu(self) -> None:
        if hasattr(self, "menu"):
            self.menu.destroy()
        self.menu = tk.Menu(self.root, tearoff=False)
        self.menu.add_command(label=self.t("refresh"), command=self.fetch)
        self.menu.add_command(label=self.t("ping_now"), command=lambda: self.fetch(force_ping=True))
        self.menu.add_command(label=self.t("hide_widget"), command=self.hide)
        self.menu.add_command(label=self.t("history"), command=self.open_history)
        self.menu.add_command(label=self.t("settings"), command=self.open_settings)
        self.menu.add_separator()
        self.menu.add_command(label=self.t("quit"), command=self.quit)

    def colors(self) -> tuple[str, str, str, str]:
        if self.settings["theme"] == "light":
            return "#FAFAFA", "#202124", "#68707A", "#E1E4E8"
        return "#161A20", "#F4F7FB", "#AEB7C2", "#2A313B"

    def apply_theme(self) -> None:
        bg, fg, muted, border = self.colors()
        self.root.configure(bg=border)
        self.root.attributes("-alpha", float(self.settings["opacity"]))
        self.card.configure(bg=bg, highlightbackground=border, highlightthickness=1)
        for label, color in ((self.flag, fg), (self.place_label, fg), (self.ip_label, fg),
                             (self.country_code_label, fg), (self.detail_label, muted), (self.status, muted)):
            label.configure(bg=bg, fg=color)

    def apply_always_on_top(self) -> None:
        self.root.attributes("-topmost", bool(self.settings["always_on_top"]))

    def restore_position(self) -> None:
        if self.settings.get("monitor_device") and self.move_to_pinned_monitor():
            return
        x, y = self.settings.get("x"), self.settings.get("y")
        if x is None or y is None:
            x = self.root.winfo_screenwidth() - 265
            y = 55
        self.root.geometry(f"+{int(x)}+{int(y)}")

    def pinned_monitor(self) -> dict | None:
        selected = self.settings.get("monitor_device")
        monitors = list_monitors(self.language)
        for monitor in monitors:
            if monitor["device"] == selected:
                return monitor
        return next((monitor for monitor in monitors if monitor["primary"]), None)

    def move_to_pinned_monitor(self) -> bool:
        monitor = self.pinned_monitor()
        if monitor is None:
            return False
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        self.root.geometry(f"+{monitor['right'] - width - 20}+{monitor['top'] + 45}")
        return True

    def start_drag(self, event: tk.Event) -> None:
        self.drag_offset = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def drag(self, event: tk.Event) -> None:
        x = event.x_root - self.drag_offset[0]
        y = event.y_root - self.drag_offset[1]
        monitor = self.pinned_monitor() if self.settings.get("monitor_device") else None
        if monitor:
            self.root.update_idletasks()
            x = max(monitor["left"], min(x, monitor["right"] - self.root.winfo_width()))
            y = max(monitor["top"], min(y, monitor["bottom"] - self.root.winfo_height()))
        self.root.geometry(f"+{x}+{y}")

    def finish_drag(self, _event: tk.Event) -> None:
        self.settings["x"], self.settings["y"] = self.root.winfo_x(), self.root.winfo_y()
        save_settings(self.settings)

    def open_menu(self, event: tk.Event) -> None:
        self.menu.tk_popup(event.x_root, event.y_root)

    def create_tray(self) -> None:
        """Tworzy ikonę trayu; pystray działa w osobnym wątku."""
        if pystray is None:
            return
        try:
            with Image.open(APP_ICON_PATH) as source:
                icon = source.convert("RGBA")
            icon.thumbnail((64, 64), Image.Resampling.LANCZOS)
        except (OSError, ValueError):
            icon = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            drawing = ImageDraw.Draw(icon)
            drawing.ellipse((4, 4, 60, 60), fill="#3478F6")
            drawing.text((25, 19), "IP", fill="white")
        self.default_tray_icon = icon.copy()
        self.tray = pystray.Icon(
            "IPInfoWidget", icon, APP_NAME, self.make_tray_menu(),
        )
        self.tray.run_detached()

    def make_tray_menu(self):
        return pystray.Menu(
            pystray.MenuItem(self.t("show_widget"), self.show_from_tray),
            pystray.MenuItem(self.t("hide_widget"), self.hide_from_tray),
            pystray.MenuItem(self.t("refresh"), self.fetch_from_tray),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(self.t("quit"), self.quit_from_tray),
        )

    def refresh_language(self) -> None:
        self.root.title(APP_NAME)
        self.build_menu()
        if self.tray is not None:
            self.tray.menu = self.make_tray_menu()
            self.tray.update_menu()

    def show_from_tray(self, _icon=None, _item=None) -> None:
        self.actions.put(self.show)

    def hide_from_tray(self, _icon=None, _item=None) -> None:
        self.actions.put(self.hide)

    def fetch_from_tray(self, _icon=None, _item=None) -> None:
        self.actions.put(self.fetch)

    def quit_from_tray(self, _icon=None, _item=None) -> None:
        self.actions.put(self.quit)

    def hide(self) -> None:
        self.root.withdraw()

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()

    def copy_ip(self, _event: tk.Event) -> str:
        """Kopiuje adres bez rozpoczęcia przeciągania całego widgetu."""
        ip_address = self.current_ip
        if not ip_address or ip_address == self.t("unknown_ip"):
            return "break"
        self.root.clipboard_clear()
        self.root.clipboard_append(ip_address)
        self.root.update_idletasks()
        self.status.configure(text=self.t("copied_ip"))
        if self.copy_notice_id is not None:
            self.root.after_cancel(self.copy_notice_id)
        self.copy_notice_id = self.root.after(1500, self.clear_copy_notice)
        return "break"

    def clear_copy_notice(self) -> None:
        self.copy_notice_id = None
        if not self.closed and self.status.cget("text") == self.t("copied_ip"):
            self.status.configure(text=self.connection_status)

    def fetch(self, force_ping: bool = False) -> None:
        if self.is_fetching or self.closed:
            return
        self.is_fetching = True
        self.status.configure(text=self.t("updating"))
        run_ping = force_ping or bool(self.settings["ping_enabled"])
        threading.Thread(target=self.fetch_worker, args=(run_ping,), daemon=True).start()

    def fetch_worker(self, run_ping: bool) -> None:
        # ipwho.is udostępnia dane przez HTTPS, bez własnego klucza API.
        # Znacznik czasu ogranicza ryzyko zwrócenia starej odpowiedzi z cache.
        request = Request(
            f"https://ipwho.is/?_={time.time_ns()}",
            headers={"User-Agent": "MyIPWidget/1.0", "Cache-Control": "no-cache"},
        )
        try:
            with urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not payload.get("success", True):
                raise URLError(payload.get("message", self.t("service_error")))
            payload["_connection_test"] = (
                {"enabled": True, **ping_host(self.settings["ping_host"])}
                if run_ping else {"enabled": False}
            )
            self.inbox.put(payload)
        except (OSError, URLError, ValueError, json.JSONDecodeError) as error:
            self.inbox.put(error)

    def process_inbox(self) -> None:
        # Tkinter modyfikujemy wyłącznie z wątku interfejsu.
        while True:
            try:
                action = self.actions.get_nowait()
            except queue.Empty:
                break
            action()
        if self.closed:
            return
        try:
            result = self.inbox.get_nowait()
        except queue.Empty:
            pass
        else:
            self.is_fetching = False
            if isinstance(result, Exception):
                self.flag_image = None
                self.flag.configure(image="", text="⚠", font=("Segoe UI Emoji", 16))
                self.update_tray_flag(None)
                self.country_code_label.configure(text="")
                self.place_label.configure(text=self.t("no_connection"))
                self.ip_label.configure(text=self.t("fetch_failed"))
                self.detail_label.configure(text=self.t("retry_hint"))
                self.connection_status = self.t("connection_unavailable")
                self.status.configure(text=self.connection_status)
                self.root.after(30_000, self.fetch)
            else:
                self.show_data(result)
                interval = max(5, int(self.settings["refresh_seconds"])) * 1_000
                self.root.after(interval, self.fetch)
        if not self.closed:
            self.root.after(250, self.process_inbox)

    def show_data(self, data: dict) -> None:
        code = data.get("country_code", "")
        country = data.get("country", self.t("unknown_location"))
        city = data.get("city", "")
        new_ip = data.get("ip", self.t("unknown_ip"))
        changed = self.current_ip is not None and new_ip != self.current_ip
        if changed:
            entry = {
                "changed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "old_ip": self.current_ip,
                "new_ip": new_ip,
                "country": country,
                "country_code": code.upper(),
            }
            entries = load_history()
            entries.append(entry)
            save_history(entries)
            self.send_change_notification(entry)
        self.current_ip = new_ip
        self.set_flag(code)
        self.country_code_label.configure(text=code.upper())
        self.place_label.configure(text=country)
        self.ip_label.configure(text=new_ip)
        details: list[str] = []
        if self.settings["show_location"] and city:
            details.append(city)
        if self.settings["show_isp"] and data.get("connection", {}).get("isp"):
            details.append(data["connection"]["isp"])
        self.detail_label.configure(text=" • ".join(details))
        test = data.get("_connection_test", {})
        if not test.get("enabled"):
            self.connection_status = self.t("connection_ok")
        elif test.get("reachable"):
            latency = test.get("latency_ms")
            ping_value = f"{latency} ms" if latency is not None else "< 1 ms"
            self.connection_status = f"{self.t('connection_ok')} • ping {ping_value}"
        else:
            self.connection_status = f"{self.t('connection_ok')} • ping {self.settings['ping_host']}: {self.t('no_response')}"
        self.status.configure(text=f"{self.t('ip_changed')} • {self.connection_status}" if changed else self.connection_status)

    def send_change_notification(self, entry: dict) -> None:
        """Pokazuje toast poza wątkiem interfejsu, aby nie zatrzymywać widgetu."""
        if Notification is None:
            return

        def show_toast() -> None:
            try:
                toast = Notification(
                    app_id=APP_NAME,
                    title=self.t("notification_title"),
                    msg=f"{entry['old_ip']} → {entry['new_ip']}\n{entry['country']}",
                    duration="short",
                )
                toast.set_audio(audio.Default, loop=False)
                toast.show()
            except Exception:
                # Brak uprawnień/obsługi toastów nie może zatrzymać widgetu.
                pass

        threading.Thread(target=show_toast, daemon=True).start()

    def open_history(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("history_title"))
        dialog.geometry("710x310")
        dialog.minsize(560, 220)
        dialog.transient(self.root)

        columns = ("time", "old", "new", "country")
        table = ttk.Treeview(dialog, columns=columns, show="headings")
        headings = {
            "time": self.t("time"), "old": self.t("previous_ip"),
            "new": self.t("new_ip"), "country": self.t("country"),
        }
        widths = {"time": 170, "old": 145, "new": 145, "country": 190}
        for column in columns:
            table.heading(column, text=headings[column])
            table.column(column, width=widths[column], anchor="w")
        for entry in reversed(load_history()):
            try:
                display_time = datetime.fromisoformat(entry["changed_at"]).strftime("%d.%m.%Y %H:%M:%S")
            except (KeyError, TypeError, ValueError):
                display_time = entry.get("changed_at", "")
            table.insert("", "end", values=(
                display_time, entry.get("old_ip", ""), entry.get("new_ip", ""),
                entry.get("country", ""),
            ))
        table.pack(fill="both", expand=True, padx=12, pady=(12, 6))

        def clear() -> None:
            save_history([])
            for item in table.get_children():
                table.delete(item)

        ttk.Button(dialog, text=self.t("clear_history"), command=clear).pack(anchor="e", padx=12, pady=(0, 10))

    def set_flag(self, country_code: str) -> None:
        """Wyświetla lokalną flagę PNG dołączoną z projektu źródłowego."""
        flag_path = FLAGS_DIR / f"{country_code.upper()}.png"
        try:
            with Image.open(flag_path) as source:
                full_flag = source.convert("RGBA")
            display_flag = full_flag.copy()
            display_flag.thumbnail((52, 52), Image.Resampling.LANCZOS)
            self.flag_image = ImageTk.PhotoImage(display_flag)
            self.flag.configure(image=self.flag_image, text="")
            self.update_tray_flag(full_flag)
        except (OSError, ValueError):
            self.flag_image = None
            self.flag.configure(image="", text=country_flag(country_code), font=("Segoe UI Emoji", 16))
            self.update_tray_flag(None)

    def update_tray_flag(self, flag: Image.Image | None) -> None:
        """Zachowuje ikonę programu w zasobniku po odświeżeniu danych IP."""
        if self.tray is None:
            return
        self.tray.icon = self.default_tray_icon
        self.tray.title = f"{APP_NAME} — {self.current_ip or ''}".rstrip(" —")

    def open_settings(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("settings_title", app=APP_NAME))
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(padx=18, pady=15)

        theme_labels = {"dark": self.t("dark"), "light": self.t("light")}
        theme_by_label = {label: code for code, label in theme_labels.items()}
        theme = tk.StringVar(value=theme_labels.get(self.settings["theme"], theme_labels["dark"]))
        refresh = tk.IntVar(value=self.settings["refresh_seconds"])
        opacity = tk.IntVar(value=round(float(self.settings["opacity"]) * 100))
        show_location = tk.BooleanVar(value=self.settings["show_location"])
        show_isp = tk.BooleanVar(value=self.settings["show_isp"])
        ping_target = tk.StringVar(value=self.settings["ping_host"])
        ping_enabled = tk.BooleanVar(value=self.settings["ping_enabled"])
        autostart = tk.BooleanVar(value=self.settings["autostart"])
        always_on_top = tk.BooleanVar(value=self.settings["always_on_top"])
        monitors = list_monitors(self.language)
        monitor_options = [self.t("any_monitor")] + [monitor["label"] for monitor in monitors]
        device_by_label = {monitor["label"]: monitor["device"] for monitor in monitors}
        selected_label = next(
            (monitor["label"] for monitor in monitors if monitor["device"] == self.settings.get("monitor_device")),
            self.t("any_monitor"),
        )
        monitor_choice = tk.StringVar(value=selected_label)

        ttk.Label(dialog, text=self.t("theme")).grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(dialog, textvariable=theme, values=tuple(theme_labels.values()), state="readonly", width=14).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(dialog, text=self.t("refresh_seconds")).grid(row=1, column=0, sticky="w", pady=4)
        ttk.Spinbox(dialog, from_=5, to=86400, textvariable=refresh, width=16).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(dialog, text=self.t("opacity")).grid(row=2, column=0, sticky="w", pady=4)
        ttk.Scale(dialog, from_=55, to=100, variable=opacity, orient="horizontal").grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Checkbutton(dialog, text=self.t("show_city"), variable=show_location).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 2))
        ttk.Checkbutton(dialog, text=self.t("show_isp"), variable=show_isp).grid(row=4, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(dialog, text=self.t("pin_monitor")).grid(row=5, column=0, sticky="w", pady=(8, 4))
        ttk.Combobox(dialog, textvariable=monitor_choice, values=monitor_options, state="readonly", width=28).grid(row=5, column=1, sticky="ew", pady=(8, 4))
        ttk.Label(dialog, text=self.t("ping_host")).grid(row=6, column=0, sticky="w", pady=(4, 4))
        ttk.Entry(dialog, textvariable=ping_target, width=30).grid(row=6, column=1, sticky="ew", pady=(4, 4))
        ttk.Checkbutton(dialog, text=self.t("ping_refresh"), variable=ping_enabled).grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 2))
        ttk.Checkbutton(dialog, text=self.t("autostart"), variable=autostart).grid(row=8, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Checkbutton(dialog, text=self.t("always_on_top"), variable=always_on_top).grid(row=9, column=0, columnspan=2, sticky="w", pady=2)

        def apply() -> None:
            try:
                refresh_value = max(1, refresh.get())
            except tk.TclError:
                messagebox.showerror(self.t("invalid_value"), self.t("refresh_error"), parent=dialog)
                return
            try:
                set_autostart(autostart.get())
            except OSError as error:
                messagebox.showerror(self.t("autostart_error"), str(error), parent=dialog)
                return
            self.settings.update({
                "theme": theme_by_label.get(theme.get(), "dark"), "refresh_seconds": max(5, refresh_value),
                "opacity": max(0.55, min(1, opacity.get() / 100)),
                "show_location": show_location.get(), "show_isp": show_isp.get(),
                "monitor_device": device_by_label.get(monitor_choice.get()),
                "ping_host": ping_target.get().strip() or DEFAULTS["ping_host"],
                "ping_enabled": ping_enabled.get(),
                "autostart": autostart.get(),
                "always_on_top": always_on_top.get(),
            })
            save_settings(self.settings)
            self.apply_theme()
            self.apply_always_on_top()
            dialog.destroy()
            if self.settings["monitor_device"]:
                self.move_to_pinned_monitor()
            self.fetch(force_ping=ping_enabled.get())

        ttk.Button(dialog, text=self.t("save"), command=apply).grid(row=10, column=0, columnspan=2, pady=(13, 0))

    def quit(self) -> None:
        self.closed = True
        self.finish_drag(None)  # type: ignore[arg-type]
        if self.tray is not None:
            self.tray.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    IPWidget().run()
