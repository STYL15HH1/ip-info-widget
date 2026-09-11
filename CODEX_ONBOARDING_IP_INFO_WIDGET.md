# CODEX ONBOARDING - IP INFO WIDGET 1.5.1

## Role of this file

This file is the persistent onboarding contract for Codex or another coding agent working on IP Info Widget.

Before changing code, inspect the actual repository. Source code is the final authority if documentation differs from implementation.

## Project identity

- Application: IP Info Widget
- Current source snapshot: 1.5.1
- Author: STYL15HH1
- Repository identity: https://github.com/STYL15HH1/ip-info-widget
- Platform: Windows
- Language/UI: Python 3.11+ with Tkinter/ttk
- Public IP API: https://ipwho.is/
- Packaging: PyInstaller one-file/windowed
- Installer: Inno Setup
- License: MIT
- Canonical version source: `core/version.py` (`APP_VERSION`)

## What the program does

IP Info Widget is a lightweight Windows desktop widget for monitoring the public IP address visible on the internet.

Primary use case: quickly verify the current public exit IP and country, especially after changing a VPN endpoint.

Current features include:

- public IP, country, ISO country code, city and ISP
- local country flags
- automatic refresh
- IP change detection
- up to 50 local history entries
- Windows IP-change notifications
- optional ping test
- Compact, Normal and Monitoring display modes
- Dark and Light themes
- opacity
- always-on-top
- monitor pinning
- draggable position with persistence
- notification-area tray
- dynamic country flag for tray/taskbar after successful lookup
- autostart in installed mode
- explicit `--portable` mode
- About window with version and STYL15HH1 attribution

Monitoring mode does NOT currently implement or claim VPN detection, IPv6 validation, DNS leak status, ASN reputation or threat intelligence.

## Required reading order

Before modifying anything:

1. Read this file completely.
2. Read `README.md`.
3. Read `CHANGELOG.md`.
4. Read `docs/ARCHITECTURE.md`.
5. Read `app.py`.
6. Read every Python module under `core/`.
7. Read every Python module under `ui/`.
8. Read every Python module under `windows/`.
9. Read `requirements.txt`.
10. Read `build_exe.bat`.
11. Read `installer.iss`.
12. If present, read `IP-Info-Widget-1.5.0-Codex-Project-Handover.pdf`.

Do not modify code during this onboarding pass.

After reading, report:

1. current application version
2. architecture map
3. responsibilities of each module
4. runtime and data flow
5. threading model
6. settings and storage model
7. Windows integrations
8. build/installer model
9. current known issues
10. any inconsistency between documentation and source

If documentation conflicts with source code, explicitly report the conflict and treat source code as authoritative.

## Architecture boundaries

Expected structure:

```text
app.py
core/
    version.py
    models.py
    storage.py
    settings.py
    history.py
    ip_service.py
    ip_monitor.py
ui/
    widget.py
    layouts.py
    settings_window.py
    history_window.py
    about_window.py
    menu.py
windows/
    monitors.py
    tray.py
    taskbar.py
    notifications.py
    autostart.py
```

Responsibilities:

- `app.py`: bootstrap and dependency composition only
- `core/`: UI-independent application logic, models, settings, history, storage, network services
- `ui/`: Tkinter windows, layouts and presentation/controller behavior
- `windows/`: Win32-specific integration

Do not move unrelated responsibilities back into `app.py`.

## Threading rule

Tkinter operations must run on the Tk main thread.

Network refresh work runs outside the UI thread and returns results through the existing queue mechanism.

System tray callbacks must not manipulate Tkinter widgets directly. Route UI actions through the Tk main-thread queue/event mechanism.

Preserve this invariant.

## Data flow

```text
IPService
    |
    v
IPMonitor
    |
    v
RefreshResult
    |
    +--> HistoryStore when IP changes
    |
    v
background worker
    |
    v
queue
    |
    v
IPInfoWidget on Tk main thread
    |--> WidgetLayout
    |--> TrayController
    |--> TaskbarIcon
    `--> notification
```

## Storage

Normal mode:

```text
%LOCALAPPDATA%\MyIPWidget\settings.json
%LOCALAPPDATA%\MyIPWidget\ip-history.json
```

Portable mode:

```text
<application folder>\config\settings.json
<application folder>\history\ip-history.json
```

Portable mode is activated explicitly:

```text
IPInfoWidget-1.5.1.exe --portable
```

Portable mode disables its autostart preference and UI control. Existing Run
entries from normal-mode copies are not removed by the current implementation.

Bundled resource paths are separate from writable data paths. In PyInstaller one-file mode resources resolve through `_MEIPASS`.

## Settings schema

Current `CONFIG_VERSION = 2`.

Defaults:

```json
{
  "config_version": 2,
  "theme": "dark",
  "opacity": 0.92,
  "refresh_seconds": 5,
  "show_location": true,
  "show_isp": false,
  "monitor_device": null,
  "ping_host": "1.1.1.1",
  "ping_enabled": false,
  "autostart": false,
  "always_on_top": true,
  "display_mode": "normal",
  "x": null,
  "y": null
}
```

Preserve backward-compatible loading. Do not discard unknown existing user values without a migration reason.

## Windows-specific rules

Pay particular attention to:

- multi-monitor coordinates
- valid negative X/Y coordinates
- monitor work areas
- DPI scaling
- RDP display topology
- borderless Tk window behavior
- taskbar icon lifecycle
- notification-area tray
- autostart registry behavior
- PyInstaller resource paths

Do not assume the primary monitor begins at `(0, 0)`.

Do not manually multiply/divide coordinates for DPI unless investigation proves that it is required.

## Resolved position issue (1.5.1)

The 1.5.0 baseline is `ef4b58b7393e11932f00dcd546ffe5bba77e443c`.
The verified fix is `0b6be2b7a0a871326f01f43587b103ad40e7e176` in the original
local repository; integration replays it onto existing remote history.

The maintainer confirmed that the test EXE resolved the invisible-widget issue
on the affected Windows machine. Do not describe the fix as pending.

- Startup prioritizes an available configured monitor; missing pins fall back
  safely to primary while retaining the device preference.
- Without a pin, visible saved coordinates are preserved, including negative x/y.
- Invalid geometry after startup/layout sizing recovers using rcWork areas.
- Visibility requires a 50 by 30 pixel intersection (or the full smaller dimension).
- Manual tray recovery runs through the Tk queue, clears monitor_device and saves
  x/y, preserving always-on-top. It remains unpinned after restart.
- No manual DPI scaling or DPI-awareness changes were introduced.
- The 13 positioning tests cover startup, recovery, restart and re-pinning.

The 1.5.0 PDF and older project documentation remain historical snapshots.
Current source and docs/ARCHITECTURE.md take precedence. Release 1.5.1 binaries
must be built and validated separately before publication.

## Network behavior

`IPService` uses:

```text
https://ipwho.is/
```

with an 8 second HTTP timeout, versioned User-Agent and no-cache behavior.

Ping uses the Windows `ping` executable with one echo request and a short timeout.

Do not add a heavy networking framework without a clear benefit.

## History

`HistoryStore.max_entries = 50`.

The first successful lookup establishes the baseline IP and does not create a change event.

A later different public IP creates an `IPChange` and writes it to history.

Malformed history should fail safely.

## Icons

Keep these concepts separate:

1. EXE/installer/shortcut icon
2. notification-area tray icon
3. taskbar/window icon

Current application icon:

```text
assets/icons/ip-info-widget.ico
```

Country flags:

```text
assets/images/flags/
```

Author image:

```text
assets/author/styl15hh1.png
```

The taskbar implementation uses native Windows HICON handles. Preserve correct handle cleanup.

Windows Explorer may cache pinned/grouped icons. Do not treat every Explorer cache behavior as an application bug.

## Build constraints

The current PyInstaller build explicitly bundles Tcl/Tk resources because an earlier standalone build failed without them.

Do not remove or simplify the following packaging behavior without testing the built EXE:

- `_tkinter.pyd`
- `tcl86t.dll`
- `tk86t.dll`
- Tkinter library data
- `_tcl_data`
- `_tk_data`
- flags
- author image
- application icon

The build script reads the version from `core/version.py`.

Expected outputs:

```text
dist/IPInfoWidget-<version>.exe
installer/IPInfoWidget-Setup-<version>.exe
```

## Change policy

For every task:

1. inspect relevant code first
2. identify the smallest coherent change
3. preserve existing behavior unless the request explicitly changes it
4. avoid unrelated refactors
5. avoid new dependencies unless justified
6. keep architecture boundaries
7. run relevant tests/checks
8. update documentation if behavior changes

If you discover an unrelated issue, report it separately instead of silently changing it.

## Testing expectations

Depending on the change, verify relevant areas:

- source startup
- built EXE startup
- public IP lookup
- city/ISP/country code
- flag loading
- refresh timer
- IP-change detection
- history
- notifications
- ping
- Compact/Normal/Monitoring modes
- themes
- opacity
- always-on-top
- drag/position persistence
- monitor selection
- negative monitor coordinates
- tray
- taskbar icon
- normal storage
- portable storage
- autostart
- About dialog
- PyInstaller build
- Inno Setup installer

Never claim a test was executed if it was not actually run.

## Required final report after implementation

After each coding task report:

1. root cause or objective
2. implementation approach
3. files changed
4. important code behavior
5. tests actually executed
6. results
7. remaining risks or limitations
8. documentation updated

## First prompt for a fresh Codex session

Use this after opening the project directory:

```text
You are taking over development of IP Info Widget.

Do not modify any files yet.

Read CODEX_ONBOARDING_IP_INFO_WIDGET.md completely, then inspect README.md, CHANGELOG.md, docs/ARCHITECTURE.md, app.py, all modules under core/, ui/ and windows/, requirements.txt, build_exe.bat and installer.iss.

If IP-Info-Widget-1.5.0-Codex-Project-Handover.pdf is present and readable, use it as additional project context.

Build a concise internal model of the application and report:
1. current version
2. source tree and module responsibilities
3. runtime/data flow
4. threading model
5. settings and storage behavior
6. Windows integrations
7. build/release process
8. current known issue(s)
9. any documentation/source inconsistencies

Source code is authoritative if documentation differs.

Do not refactor, fix, format or otherwise modify the project during this onboarding step.
```
