# Changelog

## v1.5.1 - 2026-09-11

### Fixed

- Validate saved and rebuilt widget geometry against active monitor work areas,
  preserving valid negative coordinates and recovering off-screen positions.
- Add a queued tray action to restore the widget to the primary monitor while
  preserving always-on-top and explicitly clearing the monitor pin for durable recovery.
- Preserve monitor-pin priority at startup, with safe primary placement when the
  pinned monitor is unavailable.

### Validation

- Added 13 positioning regression tests, including negative coordinates, all three
  layouts, missing monitors, manual recovery, restart and re-pinning.
- The maintainer confirmed successful physical Windows validation of the fix
  from commit `0b6be2b`; the original invisible-widget issue was resolved on the
  affected machine. This physical validation used the pre-release validation EXE.

### Documentation

- Rebuilt the public README with approved screenshots and public-IP redaction.
- Updated current version/build references while preserving historical snapshots.

## v1.5.0 - 2026-08-12

### Added

- Dynamic native Windows and notification-area icons using the current country flag.
- Explicit `--portable` mode with local `config/` and `history/` folders.
- Compact, Normal, and Monitoring widget layouts.
- Modular `core`, `ui`, and `windows` application layers.
- Architecture documentation for future contributors.
- A themed About window with application version, author identity, GitHub link, MIT license, and author avatar.

### Changed

- Settings are versioned and migrate existing values without discarding them.
- The portable settings dialog disables Windows autostart safely.
- The installer and build output target version 1.5.0.

## v1.4.1 - 2026-08-10

- Added application and installer icons.
- Added a configurable always-on-top option.
- Added IP history, connection testing, monitor pinning, autostart, themes, and opacity controls.
- Fixed Tcl/Tk packaging for the standalone Windows executable.
- Simplified the project to an English-only interface and installer.
- Removed the visible refresh status to keep the widget stable and distraction-free.
