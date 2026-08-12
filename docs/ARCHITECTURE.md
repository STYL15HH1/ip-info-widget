# IP Info Widget 2.0 Architecture

## Project map

```text
app.py                 Bootstrap and PyInstaller Tcl/Tk setup
core/
  models.py            Immutable IP, ping, refresh, and IP-change data
  storage.py           Normal and portable data/resource paths
  settings.py          Versioned settings, defaults, validation, persistence
  history.py           Bounded persistent IP-change history
  ip_service.py        HTTPS public-IP lookup and Windows ping
  ip_monitor.py        Current-IP state and change detection
ui/
  widget.py            Tk main window, state rendering, refresh coordination
  layouts.py           Compact, Normal, and Monitoring widgets
  settings_window.py   Settings dialog
  history_window.py    IP history dialog
  menu.py              Widget context menu
windows/
  taskbar.py           Native dynamic taskbar HICON lifecycle
  tray.py              Static application tray icon and its callbacks
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

## Storage

`AppPaths` is the single storage decision point.

| Mode | Settings | History |
| --- | --- | --- |
| Normal | `%LOCALAPPDATA%\MyIPWidget\settings.json` | `%LOCALAPPDATA%\MyIPWidget\ip-history.json` |
| `--portable` | `<application folder>\config\settings.json` | `<application folder>\history\ip-history.json` |

The resource directory is separate from data storage. In a PyInstaller one-file
application it resolves to `_MEIPASS`, so bundled icons and flags are found while
portable data remains alongside the executable. Portable mode disables autostart
because Windows Run entries with removable-drive paths are not dependable.

## Display layouts

Each class in `ui.layouts` receives the same `DisplayData` and decides only how
to display it. `CompactLayout` contains only flag and IP; `NormalLayout` displays
the familiar country/details card; `MonitoringLayout` adds the already available
city, ISP, and optional ping output. It does not make unsupported claims about
VPN detection, IPv6, DNS, reputation, or threats.

Mode changes rebuild only the contents of the card and preserve the top-level
window position. Monitor pinning and the theme/opacity settings are reapplied by
the controller.

## Windows icons

The application icon, tray icon, and taskbar icon are intentionally separate.

- EXE/installer/shortcut: `assets/icons/ip-info-widget.ico`.
- Tray: a static copy of the application icon (`TrayController`).
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
