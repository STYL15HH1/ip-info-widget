# Changelog

## v2.0.0 - 2026-08-12

### Added

- Dynamic native Windows taskbar icon using the current country flag.
- Explicit `--portable` mode with local `config/` and `history/` folders.
- Compact, Normal, and Monitoring widget layouts.
- Modular `core`, `ui`, and `windows` application layers.
- Architecture documentation for future contributors.

### Changed

- Settings are versioned and migrate existing values without discarding them.
- The portable settings dialog disables Windows autostart safely.
- The installer and build output target version 2.0.0.

## v1.4.1 - 2026-08-10

- Added application and installer icons.
- Added a configurable always-on-top option.
- Added IP history, connection testing, monitor pinning, autostart, themes, and opacity controls.
- Fixed Tcl/Tk packaging for the standalone Windows executable.
- Simplified the project to an English-only interface and installer.
- Removed the visible refresh status to keep the widget stable and distraction-free.
