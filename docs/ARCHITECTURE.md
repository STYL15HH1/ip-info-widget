# IP Info Widget 1.5.1 Architecture

## Project map

```text
app.py                 Bootstrap and PyInstaller Tcl/Tk setup
core/
  version.py           Canonical application version (`APP_VERSION`)
  models.py            Immutable IP, ping, refresh, and IP-change data
  storage.py           Normal and portable data/resource paths
  settings.py          Versioned settings, defaults, validation, persistence
  history.py           Bounded persistent IP-change history
  ip_service.py        HTTPS public-IP lookup and Windows ping
  ip_monitor.py        Current-IP state and change detection
ui/
  about_window.py      Themed single-instance About dialog
  widget.py            Tk main window, state rendering, refresh coordination
  layouts.py           Compact, Normal, and Monitoring widgets
  settings_window.py   Settings dialog
  history_window.py    IP history dialog
  menu.py              Widget context menu
windows/
  taskbar.py           Native dynamic taskbar HICON lifecycle
  tray.py              Dynamic country tray icon and queued callbacks
  notifications.py     Windows toast notifications
  autostart.py         Current-user Run registry entry
  monitors.py          Windows monitor enumeration and placement
```

## Data flow

```text
IPService -> IPMonitor -> RefreshResult -> IPInfoWidget -> WidgetLayout
                         |                    |              |
                         |                    +-> TaskbarIcon |
                         +-> HistoryStore      +-> TrayController
                         +-> notification
```

`IPService` does no UI work. `IPMonitor` compares a successful lookup with its
previous IP and writes a change to `HistoryStore`. The background refresh thread
places its `RefreshResult` in a queue. `IPInfoWidget` consumes that queue on the
Tk main thread, which is the only place where Tk widgets are changed.

## Application state

The widget controller owns the rendered state: current `DisplayData`, the latest
`RefreshResult`, drag coordinates, refresh timer, and the `SettingsManager` data.
The monitor owns only the prior IP used for reliable change detection. This keeps
country, ping, and UI state from being duplicated across the layout classes.

`core.version.APP_VERSION` is the canonical application version consumed by the
About window. Release and installer metadata should be updated to this same value
when preparing a new release.

## Storage

`AppPaths` is the single storage decision point.

| Mode | Settings | History |
| --- | --- | --- |
| Normal | `%LOCALAPPDATA%\MyIPWidget\settings.json` | `%LOCALAPPDATA%\MyIPWidget\ip-history.json` |
| `--portable` | `<application folder>\config\settings.json` | `<application folder>\history\ip-history.json` |

The resource directory is separate from data storage. In a PyInstaller one-file
application it resolves to `_MEIPASS`, so bundled icons and flags are found while
portable data remains alongside the executable. Portable mode disables the autostart preference and Settings control because
removable-drive paths are not dependable. It does not remove existing Run entries.

## Display layouts

Each class in `ui.layouts` receives the same `DisplayData` and decides only how
to display it. `CompactLayout` contains only flag and IP; `NormalLayout` displays
the familiar country/details card; `MonitoringLayout` adds city, ISP and optional
ping rows. The city/ISP settings still apply; absent values display as not
available. A refresh without ping displays not tested. It does not make unsupported claims about
VPN detection, IPv6, DNS, reputation, or threats.

Mode changes rebuild only the contents of the card and preserve the top-level
window position. The controller validates the sized rectangle against current `rcWork` areas,
including negative virtual-desktop coordinates. `primary_monitor`,
`rectangle_visible`, and `safe_position` in `windows/monitors.py` provide shared
placement rules. Startup gives a configured monitor pin priority over saved x/y.
`selected_monitor(..., fallback_to_primary=False)` distinguishes a missing pin
from an available display; missing pins recover to primary and save repaired x/y
while retaining the device preference. Unpinned startup validates saved x/y.
Invalid coordinates and invalid positions after a layout rebuild recover to the
primary work area. Automatic recovery saves only x/y.

The tray's `Restore widget to primary monitor` callback enqueues `restore_primary`.
The Tk queue consumer deiconifies, places, lifts, and reapplies the configured
topmost value. Manual recovery explicitly clears `monitor_device` and saves it
together with the new x/y, so the recovered position survives restart. Selecting
a monitor again in Settings restores normal pinning. If no primary monitor can
be discovered, manual recovery reveals the window but retains its pin and
coordinates; it does not persist a guessed position.

## Windows icons

The application icon, tray icon, and taskbar icon are intentionally separate.

- EXE/installer/shortcut: `assets/icons/ip-info-widget.ico`.
- Tray: the current country flag after a successful lookup, otherwise the
  application icon (`TrayController`).
- Taskbar: a process AppUserModelID and `WM_SETICON` messages set a native HICON
  created from the selected flag (`TaskbarIcon`).

At launch the taskbar gets the application icon. After a successful lookup, a
country flag HICON replaces it. Equal country codes are ignored to avoid creating
another native handle. An API failure leaves the prior valid taskbar flag in
place; a missing local flag explicitly falls back to the application icon. The
previous HICON is destroyed after it is replaced and the final one is released on
application exit.

Windows may cache an icon for a pinned shortcut or a grouped taskbar item. The
window icon update is therefore best effort: it is reliable for the window handle
but cannot force every Explorer cache to refresh immediately.

## Future additions

New lookup data belongs in `core/models.py` and `core/ip_service.py`; change
logic belongs in `core/ip_monitor.py`; persistence belongs in `core/history.py`
or `core/settings.py`; Windows APIs remain under `windows/`; and a new visual
mode belongs in `ui/layouts.py`. IPv6, DNS tests, ASN data, VPN detection,
reputation, and threat intelligence can follow those boundaries without growing
the entry point again.

## Positioning validation

Run `py -B -m unittest discover -s tests -v` on Windows with Tkinter available.
The 13 tests exercise real Tk windows with synthetic work areas and isolated
settings, covering pin-first startup, missing-pin fallback, negative coordinates,
all layouts, queued manual recovery, topmost, simulated restart and re-pinning.
They do not substitute for physical multi-monitor, DPI or RDP testing.

The maintainer confirmed successful physical validation of the 1.5.0 test EXE
built from the position-fix commit. Version 1.5.1 is a bug-fix release preparation;
its final EXE and installer have not yet been built or published.
