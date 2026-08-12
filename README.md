# IP Info Widget

IP Info Widget is a small Windows desktop widget that keeps your current public
IP address and approximate exit location visible at a glance. It is useful for
people who often change VPN servers and want a persistent, uncomplicated way
to verify that their public IP and country have really changed.

The application queries [ipwho.is](https://ipwho.is/) over HTTPS. It refreshes
every 5 seconds by default, keeps a local change history, and can display a
Windows notification when the public IP changes.

## Screenshots

| VPN exit locations | Widget controls |
| --- | --- |
| ![Widget showing a Poland connection](docs/screenshots/widget-poland.png) ![Widget showing a Romania connection](docs/screenshots/widget-romania.png) | ![Right-click context menu](docs/screenshots/context-menu.png) |
| ![Widget showing a Switzerland connection](docs/screenshots/widget-switzerland.png) ![Widget showing a United States connection](docs/screenshots/widget-united-states.png) | ![Settings window](docs/screenshots/settings.png) |

## Features

- Public IPv4 address, country, ISO code, city, ISP, and bundled country flags.
- Dynamic **taskbar** icon: after a successful lookup it changes to the current
  country's flag. The system-tray icon intentionally remains the IP Info Widget
  application icon.
- IP change detection, Windows notifications, and a local history of the last
  50 changes.
- One-click IP copying, manual refresh, and an optional Windows ping check.
- Compact, Normal, and Monitoring layouts. Normal is the default.
- Dark/light themes, 55–100% opacity, draggable position, multi-monitor pinning,
  optional always-on-top behavior, and optional Windows sign-in startup.
- `--portable` mode, which keeps settings and history beside the executable.

## Display modes

| Mode | Visible information |
| --- | --- |
| **Compact** | Country flag and public IP only. |
| **Normal** | Country, ISO code, flag, IP, and optional city/ISP. |
| **Monitoring** | Normal essentials plus city, ISP, and the real ping result when a ping has been run. It deliberately does not claim VPN, IPv6, or DNS status. |

Switch the mode in **Settings → Display mode**. The change is immediate and
the current window position, theme, opacity, and selected monitor are retained.

## Settings

| Option | Description |
| --- | --- |
| Display mode | Choose Compact, Normal, or Monitoring. |
| Theme / Opacity | Select Dark or Light and set 55–100% opacity. |
| Refresh interval | Check the public IP every 5 seconds to 24 hours. |
| Show city / provider | Control the details in the normal layout. |
| Pin to monitor | Keep the widget in the work area of a chosen display. |
| Ping host / Test ping | Choose an optional connectivity target and run it automatically or from the menu. |
| Start with Windows | Create a current-user Windows startup entry (normal mode only). |
| Always on top | Keep the widget over other windows, or let it be covered normally. |

## Portable mode

Run either the source application or the packaged executable with `--portable`:

```text
python app.py --portable
IPInfoWidget.exe --portable
```

Portable mode writes no settings or history to `%LOCALAPPDATA%`. Instead it
creates these folders next to the application:

```text
IP Info Widget/
├── IPInfoWidget.exe
├── config/settings.json
└── history/ip-history.json
```

Windows autostart is disabled in portable mode because a USB drive letter may
change and would leave an invalid startup entry. Normal installed mode remains
unchanged and stores data in `%LOCALAPPDATA%\MyIPWidget`.

## Run from source

1. Install Python 3.11 or newer for Windows and enable **Add Python to PATH**.
2. Open a terminal in this folder.
3. Run `python -m pip install -r requirements.txt`.
4. Run `python app.py` or `python app.py --portable`.

## Build the installer

Install [Inno Setup](https://jrsoftware.org/isdl.php), then run `build_exe.bat`.
It installs the build dependencies, creates `dist/IPInfoWidget.exe`, and builds
`installer/IPInfoWidget-Setup-2.0.0.exe`. End users only need the installer.

The executable includes the application icon and all 252 local country flags.
The packaged file initially uses the regular application icon; the window's
native taskbar icon changes to a country flag after the first successful lookup.
Windows can cache icons for pinned or grouped taskbar items, so unpinning and
reopening a previously pinned shortcut may be necessary to observe updates.

## Privacy

The program sends a lookup request to `https://ipwho.is/` to obtain the public
address and approximate location. Locally it stores widget settings and up to
50 IP-change entries. Use **IP change history → Clear history** to remove them.

## Development

See [Architecture](docs/ARCHITECTURE.md) for module boundaries, data flow, and
safe extension points.

## License

This project is released under the [MIT License](LICENSE).
