# IP-INFO-WIDGET — Project Documentation and Knowledge Preservation

> **Purpose.** This is the long-term technical and historical reference for IP-Info-Widget. It combines the current repository state with the preserved development conversation. Implementation facts are based on the current source unless marked otherwise. Historical statements come from the preserved conversation. Anything not evidenced by either is marked **Unknown / Not confirmed**.

## 1. Project identity

| Item | Current evidence |
| --- | --- |
| Name | IP Info Widget / IP-Info-Widget |
| Canonical repository | https://github.com/Stylishh1/ip-info-widget |
| Repository-name discrepancy | The supplied brief spells `STYL15HH1`; the actual created repository and remote are `Stylishh1`. Treat the latter as canonical. |
| Platform | Windows, x64 installer target |
| Language / UI toolkit | Python; Tkinter/ttk |
| Main libraries | Pillow, pystray, winotify; PyInstaller at build time |
| External service | `https://ipwho.is/` over HTTPS |
| Distribution | PyInstaller one-file GUI EXE, wrapped by Inno Setup installer |
| Current determinable version | 1.4.1 (`installer.iss`, GitHub release v1.4.1) |
| Status | Public, working release; feature-complete for the discussed scope, with known technical debt below |
| License | MIT |

**Concise description.** IP Info Widget is a compact, draggable Windows widget that continuously displays the current public IP and approximate egress location, aimed at people who switch VPN endpoints and need persistent visual confirmation of the resulting public address.

**Technical description.** `app.py` creates a borderless Tkinter widget, fetches JSON from ipwho.is in a daemon worker thread, transfers results to the UI thread through queues, compares each received IP with in-memory state, records changes locally, optionally issues a Windows toast, and renders location data plus a bundled country flag. It persists user settings/history under `%LOCALAPPDATA%\MyIPWidget`, integrates with Windows tray, Run-key autostart, monitor enumeration, clipboard, and topmost windows, then is bundled with Tcl/Tk payloads by PyInstaller and installed by Inno Setup.

## 2. Original problem and intended users

**Confirmed historical facts.** The application was shaped around the request for a persistent IP widget, monitoring changes when using a VPN, with country/location display and a choice whether the widget stays above other applications. The user explicitly described it as useful for someone who “often uses a VPN and wants to monitor”.

**Supported inference.** Checking a public-IP web page manually interrupts work and does not provide an always-visible, change-oriented signal. A persistent desktop card makes changes in VPN exit address/country visible without repeatedly opening a browser.

It is intended for Windows users who frequently change VPN servers, validate tunnel reconnections, monitor unexpected public-route changes, or simply need a small public-IP/location indicator. It does not prove that a VPN is secure, leak-free, or connected; it reports the public information returned by the external IP service.

## 3. Evolution timeline

| Stage | Evidence and result |
| --- | --- |
| Initial widget | Conversation/code establish a light Windows public-IP widget with local flags, IP/location retrieval, drag positioning, theme and opacity. Exact pre-repository chronology is **Unknown / Not confirmed**. |
| VPN/IP monitoring | Default refresh set to 5 seconds to make VPN/IP changes visible quickly; current IP is retained in memory and compared on refresh. |
| Monitoring utilities | IP-change toast/history, manual/automatic ping, monitor pinning, autostart, tray actions, settings and context menu were present by the first public release. Exact request order is not fully recoverable. |
| Always-on-top option | Explicit user request. `always_on_top` defaulted to `True`; Settings can disable `-topmost`. |
| Icon work | Explicit request supplied visual references. A multi-size ICO was produced and embedded into EXE, installer, shortcuts, window, and tray. |
| Tcl/Tk packaging failure | Version 1.2.0 raised “Can't find a usable init.tcl”. Root cause: Tcl/Tk data placed under `tcl\...` while PyInstaller runtime expects `_tcl_data`/`_tk_data`. Fixed in 1.2.1 by bundling the expected directory names and setting `TCL_LIBRARY`/`TK_LIBRARY`. Start test passed. |
| Localization attempt and rollback | Polish/English automatic/manual localization was added in 1.3.0. Settings rendered blank due to an error during control creation. User chose English-only; 1.4.0 removed the selector and installer localization. Dead localization code remains in `app.py`. |
| Status-line removal | User reported distracting alternating “Internet: OK” / “Updating…”. In 1.4.1 the status label remained for internal messages but is deliberately not gridded, so no status row is visible. |
| Publishing | Git repository initialized, MIT/LICENSE/docs added, public repository and v1.4.1 release published. README/screenshots added in the second commit. |

No evidence supports treating any absent feature as rejected except the localization implementation, which was explicitly superseded by English-only UI. SmartScreen was discussed: it is caused by an unsigned new installer; code signing was identified as the durable solution but **not implemented**.

## 4. Complete feature inventory

| Feature | Status | User behavior / implementation / files | Edge cases |
| --- | --- | --- | --- |
| Public IP lookup | Implemented | HTTPS request to `https://ipwho.is/?_=<ns>`; `fetch_worker`, `show_data` in `app.py`. | 8 s request timeout; errors become an offline/error UI and retry after 30 s. |
| Location/flag display | Implemented | Country, ISO code, city and optional ISP; local `assets/images/flags/<ISO>.png`; `set_flag`. | Missing/bad flag falls back to flag emoji. |
| IP change detection | Implemented | In-memory `current_ip`; non-first differing value creates history and toast. | First successful fetch never creates a change event; an API failure does not erase `current_ip`. |
| History | Implemented | Last 50 JSON entries in `%LOCALAPPDATA%\MyIPWidget\ip-history.json`; Treeview dialog / clear button. | Persists restarts; malformed file yields empty history. |
| Windows toast | Implemented, optional runtime degradation | `winotify.Notification` in a daemon thread. | Import, toast, audio, or permission failures are swallowed. |
| Ping | Implemented | Windows `ping -n 1 -w 1500`; manual menu item or each fetch if enabled. | Internal status only in v1.4.1; current visible UI does not show ping result. |
| Settings | Implemented | Modal `Toplevel`, `open_settings`. | Autostart error shows a message box; refresh parses an integer. |
| Theme/opacity | Implemented | Dark/light colors; alpha 55–100%. | Applies immediately after Save. |
| Monitor pinning | Implemented | Win32 monitor enumeration; position near selected monitor upper-right. | Missing selected display falls back to primary display. |
| Drag/position persistence | Implemented | Mouse drag and `x`,`y` settings. | Pinned monitor constrains drag. |
| Always on top | Implemented | `root.attributes('-topmost', value)`. | Defaults to on. |
| Autostart | Implemented | Current-user `HKCU\...\Run` named `IP Info Widget`. | Requires writable registry; legacy value is removed. |
| Tray/menu/hide | Implemented, optional tray degradation | pystray icon; show/hide/refresh/quit. Right-click widget menu includes ping/history/settings. | If pystray import fails, widget continues without tray. |
| Icons | Implemented | App ICO is EXE, installer, shortcuts, window and tray asset. | Tray falls back to drawn blue “IP” glyph if ICO cannot load. |
| Localization | Deprecated/incomplete residue | Current `self.language = 'en'`; visible UI/installer are English. | `TRANSLATIONS`, `detect_system_language`, `resolve_language`, `refresh_language` remain; `locale` is no longer imported, so calling detect function would fail. |
| Visible refresh status | Deprecated | Status object remains but is not placed on the widget. | Invisible errors/ping/copy messages are a deliberate UX trade-off. |

## 5. User interface and interaction reference

### Widget

The root is borderless (`overrideredirect(True)`) and has a framed card with 16 px horizontal/13 px vertical padding. It is not a conventional resizable window. The hierarchy is: **country name**, then **ISO code and bold monospace public IP**, then **flag and detail line** (city; optional ISP separated by a bullet). The country code is 16 pt Cascadia Mono bold; IP is 11 pt Cascadia Mono bold; country is Segoe UI Semibold 10; details are Segoe UI 8. Dark colors are `#161A20` background, `#F4F7FB` foreground, `#AEB7C2` muted, `#2A313B` border; light values are defined in `colors`.

Left-clicking the IP copies it to clipboard. Other left-button drag bindings move the widget; release persists its coordinates. Right-click opens: **Refresh now**, **Test connection now**, **Hide widget**, **IP change history**, **Settings**, **Quit**. Hide withdraws the root; tray Show restores/deiconifies/lifts it. No icon-bearing toolbar, refresh icon, clipboard icon, close icon, or hover-state control exists in current code; actions are text menu commands. The status label is intentionally invisible in 1.4.1.

### Settings

The modal, non-resizable dialog is `Settings — IP Info Widget`, with Theme combobox, refresh Spinbox, opacity Scale, Show city/ISP checkboxes, monitor combobox, ping host entry, ping-on-refresh checkbox, autostart checkbox, always-on-top checkbox, and Save. Saving persists then applies theme/topmost, moves to a pinned monitor, and triggers an update. There is no Cancel button; closing discards uncommitted Tk variable edits.

### History, notifications and tray

History is a 710×310 (minimum 560×220) Treeview: changed-at, old IP, new IP, country, plus Clear history. Toast title is “Public IP changed”; body includes old → new IP and country. Tray uses application ICO, title `IP Info Widget — <current ip>`, and Show/Hide/Refresh/Quit. The widget’s title/icon may not be visible normally because it is borderless.

## 6. Iconography and visual assets

| Asset/group | Format and source | Actual role |
| --- | --- | --- |
| `assets/icons/ip-info-widget.ico` | Multi-resolution ICO, 16/20/24/32/40/48/64/128/256 confirmed in earlier build inspection | Canonical app icon; PyInstaller `--icon`, Inno `SetupIconFile`, Windows shortcuts/uninstall display icon, Tk `iconbitmap`, tray source. |
| `ip-info-widget.png` | 1024×1024 PNG | Raster companion/export; current code does not load it. |
| `ip-info-icon.png` and `ip-info-icon-source.png` | 1254×1254 PNGs | Source/working visual assets; current code does not load them. Exact provenance/design history: **Unknown / Not confirmed**. |
| Country flags | 252 local PNG files, keyed by ISO-style code | Dynamic flag beside location. `set_flag` converts/resizes to max 52×52, no external image request. The code comment says they came from an original My-IP-Widget asset set; original licensing/provenance is **Unknown / Not confirmed** and should be verified before future redistribution changes. |
| Screenshots | `docs/screenshots/*.png` | Documentation examples only; four VPN exit locations, context menu, settings. |

No separate settings/network/refresh/clipboard/history/ping/theme/monitor/startup/notification icons are implemented. These concepts use native text controls, generic window close control, country flags, or the shared app icon. The fallback tray visual is a blue circle with white “IP”, generated at runtime only when ICO loading fails.

## 7. Architecture

```text
User actions / timer / tray callbacks
        │
        ▼
IPWidget (Tk UI thread) ──► fetch() ──► daemon worker
        ▲                                  │ HTTPS JSON + optional ping.exe
        │ actions/inbox queues              ▼
        └──────── process_inbox() ◄──── result/error
                 │
       render widget / compare IP / persist history / toast
                 │
     JSON settings/history, flags, Win32 monitor + registry + tray
```

`app.py` is a single-module application. Tk state is modified only in the UI thread; the network worker puts `dict | Exception` into `inbox`, and pystray callbacks put callables into `actions`. No formal application/domain/data-access layers exist.

## 8. Source-code component analysis

| Component | Responsibility, dependencies and side effects |
| --- | --- |
| Constants/`DEFAULTS` | Names, LocalAppData paths, asset paths and default settings. `load_settings` merges persisted JSON over defaults; unknown keys survive subsequent save. |
| `load_*` / `save_*` | UTF-8 JSON persistence. Read OSError/JSON errors degrade to defaults/empty; writing errors are not caught. History writes last 50. |
| `list_monitors` | ctypes structures + `EnumDisplayMonitors`/`GetMonitorInfoW`; produces work-area rectangles and device IDs. Windows-specific. |
| `ping_host` | Calls OS ping with 1.5 s Windows timeout and 3 s process timeout; regex accepts English `time` and Polish `czas`. Returns `{reachable, latency_ms}`. |
| `set_autostart` | Writes/removes the user Run registry value. Raises OSError to Settings caller. |
| `IPWidget.__init__` | Creates UI, event bindings, menu, restores placement, starts tray and first fetch/poll. |
| `fetch_worker` / `process_inbox` | Separate blocking network access from Tk. Error result makes warning/offline presentation and schedules 30s retry; success schedules configured interval. |
| `show_data` | Change comparison, history/toast, labels/flag/detail rendering, internal connection state. |
| `open_history` / `open_settings` | Toplevel interface and persistence. |
| `quit` | Persists position, stops tray, destroys root. |

## 9. Public IP and location retrieval

The worker makes `GET https://ipwho.is/?_=<time.time_ns()>` with `User-Agent: MyIPWidget/1.0` and `Cache-Control: no-cache`. The cache-busting timestamp is intended to reduce stale response risk. It decodes JSON and treats `success: false` as an error. Fields used: `ip`, `country`, `country_code`, `city`, `connection.isp`; the app does not derive location itself. Request timeout is 8 seconds, with no exponential backoff or alternative provider. A failure presents warning glyph/no connection text and retries after 30 seconds.

## 10. IP-change detection state transition

```text
startup → fetch → first successful payload → current_ip = payload.ip (no event)
timer/manual fetch → payload → compare payload.ip to current_ip
  unchanged → render current data → schedule next configured refresh
  changed → append history entry → start toast thread → current_ip = new value → render
error → render error state → retry in 30 seconds
```

Timestamps are local aware timestamps via `datetime.now().astimezone().isoformat(timespec='seconds')`. Only public IP inequality triggers an event; a location/ISP change under the same IP does not. Current IP is process-memory only; after restart, the first value does not compare to previous session history.

## 11. IP history

Records are JSON objects with `changed_at`, `old_ip`, `new_ip`, `country`, `country_code`; city/location is not separately stored. The file is `%LOCALAPPDATA%\MyIPWidget\ip-history.json`; therefore it survives restart for that Windows user. `save_history` retains last 50 entries. The dialog displays local formatted timestamp, old/new address and country; Clear history writes `[]` and removes table rows. Corrupt/invalid history reads as empty; write failure is unhandled.

## 12. Ping/connectivity testing

Ping does not obtain public IP and public-IP success does not prove the configured ICMP target responds; they are separate checks. Default host: `1.1.1.1`. A manual context-menu command passes `force_ping=True`; automatic execution occurs with each lookup only when `ping_enabled` is true. The worker runs ping after an ipwho.is payload, not independently. Result is calculated and placed in `_connection_test`; in v1.4.1 it only updates invisible status text, so ping is operational but has no current user-visible result. This is a documented UX limitation.

## 13. Complete settings reference

| Key/default | Allowed values | Effect/persistence |
| --- | --- | --- |
| `theme: dark` | `dark`, `light` | Colors, persisted JSON. |
| `refresh_seconds: 5` | UI 5–86400; Save clamps to ≥5 | Successful-fetch timer. |
| `opacity: 0.92` | UI 55–100%, clamped .55–1 | Tk alpha. |
| `show_location: true` | Boolean | Include API city. |
| `show_isp: false` | Boolean | Include `connection.isp`. |
| `monitor_device: null` | Any monitor device ID/null | Pinned placement and drag constraints. |
| `ping_host: 1.1.1.1` | Nonblank text; blank resets default | ping command target. |
| `ping_enabled: false` | Boolean | Automatic ping after lookup. |
| `autostart: false` | Boolean | HKCU Run entry. |
| `always_on_top: true` | Boolean | `-topmost` window attribute. |
| `x`, `y`: null | integers/null | Persisted manual widget location. |

Historical residue: a saved `language` key may exist from 1.3.x. It is ignored by current runtime; `load_settings` preserves it because it merges rather than filters.

## 14. Windows integration

Windows APIs/libraries cover: ctypes monitor enumeration; `winreg` Run key; `subprocess` Windows ping; Tk clipboard/topmost/alpha/window geometry; `pystray` notification-area icon; `winotify` toast; Inno shortcut/uninstall metadata. Installer requires administrator/UAC, targets x64-compatible systems and installs in `{autopf}\IP Info Widget` (normally `C:\Program Files\IP Info Widget`). Start-menu entry is created; desktop shortcut is optional/unchecked. Inno Setup provides standard uninstallation through its generated uninstaller; uninstall behavior beyond default Inno behavior is **Unknown / Not confirmed**.

## 15. Build and distribution

```text
Python source + assets
  → build_exe.bat installs requirements + PyInstaller
  → one-file, windowed IPInfoWidget.exe
  → Inno Setup ISCC.exe compiles installer.iss
  → installer/IPInfoWidget-Setup-1.4.1.exe
  → Program Files installation / shortcuts / uninstaller
```

`build_exe.bat` prefers `py`, otherwise `python`; installs/upgrades pip and installs `requirements.txt` plus PyInstaller. It explicitly adds `_tkinter.pyd`, Tcl/Tk DLLs, tkinter package, `_tcl_data`, `_tk_data`, flags, app ICO, all winotify files, and hidden `_tkinter`. The explicit Tcl/Tk inclusions are non-negotiable because automatic detection failed in the recorded environment. Python 3.13.13 and PyInstaller 6.22.0 were used for recorded builds; README declares Python 3.11+. End users need neither Python nor packages. Inno Setup 6/7 is required on the developer machine. SmartScreen warning is expected for the currently unsigned installer; Authenticode signing is not configured.

## 16. Repository structure

```text
app.py                                  complete application
assets/icons/                           canonical ICO + PNG source/export assets
assets/images/flags/                    252 bundled flags
docs/screenshots/                       README examples
requirements.txt                        runtime dependencies
build_exe.bat                           PyInstaller + Inno build automation
installer.iss                           installer metadata/files/shortcuts
README.md / CHANGELOG.md / LICENSE      public project material
.gitignore                              ignores builds, EXE outputs and local artifacts
IP-INFO-WIDGET-PROJECT-DOCUMENTATION.md master knowledge document
```

Ignored local artifacts include `build*`, `dist*`, installer EXEs, `.spec`, pycache and virtual environments. `MyIPWidget.spec` is presently local/untracked by ignore rule, not repository source.

## 17. Dependency inventory

| Dependency | Role | Runtime/end-user |
| --- | --- | --- |
| Python stdlib: tkinter, urllib, json, ctypes, winreg, subprocess, threading | UI, network, storage, Windows integration | Runtime in source; bundled into EXE, not end-user install. |
| Pillow >=10 | Flag/image and tray ICO processing | Runtime; bundled. |
| pystray >=0.19,<0.20 | system tray | Runtime optional; degradation if import fails. |
| winotify >=1.1,<2.0 | Windows toast | Runtime optional; degradation if import fails. |
| PyInstaller | EXE bundling | Build-time only. |
| Inno Setup 6/7 | Windows installer | Build-time only. |
| ipwho.is | public IP/location API | Online operational dependency. |

## 18. Privacy and security

The app sends an HTTPS request to ipwho.is; that service observes the requester’s public IP and receives standard HTTP metadata including the custom user agent. It receives the service’s IP/location/ISP response; country/city are approximate provider-supplied data, not GPS. It stores settings and up to 50 IP-change records locally. No credentials, authentication tokens, telemetry, analytics, cloud account, advertising SDK, or additional intentional data upload is implemented. Ping sends ICMP/Windows ping traffic to the configured host.

Relevant considerations: API availability/trust and malformed data; Python/package supply chain at build time; unsigned EXE/installer and SmartScreen reputation; UAC installer privileges; public IP history being sensitive on a shared profile. API responses are not schema-validated beyond JSON/success and may be untrusted. No risk claim beyond those evidenced considerations is made.

## 19. Error handling and failure modes

| Condition | Current behavior |
| --- | --- |
| No internet/API unavailable/invalid JSON | Worker puts error; UI shows warning, no-connection/retry text, then 30-second retry. |
| Missing location/country/ISP | Defaults unknown location; omits empty city/ISP; invalid code flag fallback. |
| Ping failure | Returns unreachable/none internally; not visibly surfaced in v1.4.1. |
| Monitor disappears | Selected device not found → primary monitor fallback if available. |
| Settings/history unreadable | Defaults/empty results. |
| Settings/history unwritable | Save functions may raise; Settings catches autostart failure, not all JSON write failure. |
| Flag/ICO unavailable | Flag emoji or generated tray glyph; Tk window icon failure is ignored. |
| Notification unsupported/fails | Silently ignored. |
| Tcl/Tk absent from EXE | Previously fatal; fixed through explicit bundle paths, but must be regression-tested after build changes. |

## 20. Design decisions

| Decision | Problem/options | Selected solution and consequence |
| --- | --- | --- |
| Persistent compact widget | Browser checks vs desktop indicator | Borderless draggable desktop card; quick visibility but less conventional window chrome. |
| 5-second default | VPN server changes need prompt feedback | Fast polling; more API/network activity than a long interval. |
| Local flags | External image loading vs bundled assets | 252 PNGs bundled; predictable offline rendering, larger package. |
| In-memory comparison | Persist baseline vs avoid startup false event | First startup fetch does not notify; cross-restart change detection is absent. |
| One-file PyInstaller | Simple sharing vs directory bundle | Easy installation; Tcl/Tk packaging complexity required manual fix. |
| Inno Setup | Windows installer/shortcuts/UAC | Standard Program Files distribution; admin prompt. |
| Settings-controlled topmost | Always visible vs normal overlap | Default topmost, user may disable. |
| English-only UI | Localization flexibility vs stability | User chose stability after settings dialog regression; obsolete localization residue should be removed later. |
| Hidden status row | Connectivity feedback vs visual flicker | Eliminates distracting UI; removes visible ping/error/copy feedback. |

## 21. Rejected/superseded alternatives

- **Automatic and manual Polish/English localization:** implemented during 1.3.0, then superseded after settings failed to render; user explicitly requested all-English. It may be revisited only with tests around Settings creation.
- **Visible “Internet: OK” / “Updating…” status:** explicitly removed in 1.4.1 because it flickered. It should not return unless redesigned non-disruptively.
- **Unsigned installer warning workaround:** no workaround was implemented. Signing with Authenticode was identified as the durable future solution; certificate acquisition/configuration is not confirmed.
- Any other rejected idea: **Unknown / Not confirmed**.

## 22. Development problems and solutions

1. **Tcl/Tk launch failure.** Symptom: `_tkinter.TclError: Can't find a usable init.tcl` in a PyInstaller one-file EXE. Root cause: manually included Tcl directories did not match PyInstaller runtime hook paths. Fix: package libraries as `_tcl_data`/`_tk_data`, set `TCL_LIBRARY`/`TK_LIBRARY` early when frozen, and include `_tkinter` and DLLs. Verified archive contents and five-second EXE startup.
2. **Blank Settings after localization.** Symptom: settings title but empty white dialog. Root cause: a localization-era control-construction regression; exact exception is **Unknown / Not confirmed**. Fix: remove language selector/runtime switching and use English. Settings control-count and startup were tested.
3. **No satisfactory post-install icon report.** The installer process was halted by SmartScreen before installation, so no installed file/shortcut existed to inspect. Tray was subsequently changed to load the canonical app ICO rather than dynamic country flags. The final installed-shortcut/icon visual result is not independently confirmed in preserved evidence.
4. **Status flicker.** User reported alternating states during refresh. Fix: keep label internal but do not grid it.

## 23. Current-state snapshot and limitations

The repository's `main` has release v1.4.1 and subsequent README/screenshot documentation commit. Current source implements the features in Sections 4–14. Known limitations/technical debt: single 732-line module; no automated tests; no schema validation/alternate API; no persisted previous-IP baseline; ping results and clipboard/error feedback are invisible; Polish translation dictionary/dead functions remain; `detect_system_language` references `locale` after import removal if invoked; unsigned public installer triggers SmartScreen; UI uses legacy encoding-corrupted Polish comments/unused strings in source; flag asset provenance/license needs verification. The GitHub release contains v1.4.1 installer; later documentation is on `main`, not necessarily in the source archive attached to that tag.

## 24. Roadmap / future improvements

**Discussed/confirmed:** acquire/configure Authenticode signing to reduce SmartScreen warnings; reconsider localization only with a tested Settings workflow.

**New recommendations (not historical requirements):** remove inactive localization code or reintroduce it with tests; show ping/copy errors in a non-flickering toast/tooltip; add unit tests for persistence/change detection/settings; persist a last-known IP baseline if cross-restart detection is desired; document/verify flag licenses; add CI build and checksum/signing workflow; add an API fallback/provider configuration.

## 25. Testing

**Confirmed tested during development:** Python syntax compilation; asset ICO inspection; PyInstaller archive inspection for `_tkinter`, DLLs and Tcl/Tk data; app EXE startup for five seconds after Tcl fix and subsequent versions; settings dialog control render check after English-only rollback; status row absence; Inno compilation; GitHub release upload. Screenshots demonstrate widget/settings/menu states. The final release asset’s SHA-256 on GitHub release page is `bd76397e481cee4d6c39874993255e66db214c1661bebd5b626dab2133445588`.

**Should be tested before/after future release:** clean Windows install/uninstall; actual shortcut and EXE icon rendering; tray behavior; start with no network/API outage; forced IP and VPN endpoint change; history survives restart and cap 50; autostart registry; monitor removal/multiple displays; both themes/opacity; manual and auto ping; API malformed/missing fields; settings write failure; SmartScreen/signature status.

## 26. Operational guide

Run source with Python 3.11+ on Windows: `python -m pip install -r requirements.txt`, then `python app.py`. Right-click widget for operational commands; click the IP to copy. Settings/history are under `%LOCALAPPDATA%\MyIPWidget`.

Build by installing Inno Setup, then double-click `build_exe.bat`; output is `installer\IPInfoWidget-Setup-1.4.1.exe`. For new version numbers update `installer.iss`, build-script output text, README/changelog, build, start-test, then create Git tag/release and attach installer. Add an app icon by replacing canonical ICO and retain the PyInstaller/Inno references. Add a setting by extending `DEFAULTS`, UI variable/control, `apply()` update, and documentation; test persisted legacy settings. Add data fields by validating `payload` in `show_data`, deciding privacy/UI implications, and keeping worker/UI separation. Add a provider behind a dedicated retrieval abstraction rather than scattering URL calls.

## 27. If rebuilding from scratch

1. Build a Windows Python/Tkinter borderless draggable card.
2. Query an HTTPS public-IP/location service in a daemon thread; deliver results on the Tk thread through a queue.
3. Render country/code/IP/city/ISP and locally bundled flags.
4. Keep current IP in state; on later mismatch, append a bounded JSON history and optional Windows toast.
5. Persist appearance, position, monitor, ping and Run-key settings in LocalAppData.
6. Implement text context/tray menus; mouse IP copy; selected-monitor geometry; topmost/alpha/theme.
7. Add optional `ping.exe` test separately from IP lookup.
8. Bundle flags/icon/Tcl/Tk explicitly with PyInstaller one-file GUI build, under `_tcl_data`/`_tk_data`.
9. Create x64-compatible Inno Setup installer with Program Files, Start Menu, optional desktop shortcut and shared ICO.
10. Test VPN change, outage, clean install and all settings before release.

## 28. AI development context

**Intent/non-negotiables:** a small persistent Windows public-IP/VPN-exit monitor; bundled flags; IP change history/toast; settings; tray; topmost choice; English current UI; hidden refresh-status row. Do not remove Tcl/Tk explicit packaging, preserve one-file start behavior, do not reintroduce a flickering status row, and do not claim IP data proves VPN security.

**Safe modification rules:** inspect `DEFAULTS`, stored JSON compatibility, worker/UI queue boundaries, build script and installer together. Test frozen EXE whenever imports/assets/Tkinter change. Test Settings rendering whenever localization/control layout changes. Preserve the ICO references in all four places (PyInstaller, installer, Tk, tray). Do not access Tk widgets in worker threads. Ensure release version, changelog, README and installer name agree.

**Regression hotspots:** Tcl paths, `Path(__file__)` asset paths in a frozen EXE, optional import degradation, monitor fallback, hidden status semantics, registry writes, the retained localization residue, and GUI-only errors that syntax checks miss.

## 29. Requirements matrix

| ID | Requirement | Source | Status | Implementation |
| --- | --- | --- | --- | --- |
| R-01 | Persistent public-IP/location widget | Conversation + implementation | Implemented | `IPWidget`, ipwho.is, Tk UI |
| R-02 | VPN-friendly change monitoring | Conversation + implementation | Implemented | 5s default, comparison/history/toast |
| R-03 | Configurable topmost | Conversation | Implemented | `always_on_top`, Settings |
| R-04 | App/installer icon | Conversation | Implemented | ICO/PyInstaller/Inno/tray |
| R-05 | Reliable frozen Tkinter EXE | Development history | Implemented, regression risk | `_tcl_data`, `_tk_data`, early env vars |
| R-06 | English-only current experience | Confirmed decision | Implemented | `self.language='en'`, Inno English |
| R-07 | No visible status flicker | Conversation | Implemented | status label ungridded |
| R-08 | Public source/release package | Conversation + repository | Implemented | GitHub repository/release |
| R-09 | Authenticode signing | Confirmed future discussion | Planned / not implemented | No signing command/certificate |
| R-10 | Full automated test suite | New recommendation | Not implemented | No test files |

## 30. Final executive summary

IP Info Widget is a Windows/Tkinter public-IP and approximate-location monitor designed chiefly for rapid VPN endpoint validation. It uses ipwho.is over HTTPS, displays bundled flags/location information, compares public addresses in memory, saves a bounded local history, and can issue a Windows toast. It integrates with Windows settings, tray, Run-key autostart, monitor geometry and a PyInstaller/Inno distribution pipeline. The most consequential choices were fast default polling, local flags, explicit Tcl/Tk packaging, user-controlled topmost behavior, an English-only rollback after localization broke Settings, and removal of visible refresh feedback to avoid flicker. Future work should prioritize signing, cleanup/testing of localization residue, and full clean-machine installer validation.

## Completeness check

- [x] Repository structure, source, README, changelog, requirements, build script, installer, config and Git history inspected.
- [x] Icons, all 252 flag assets as a set, and documentation screenshots inspected/inventoried.
- [x] Current code architecture, UI, persistence, API, Windows integration, packaging, privacy and failure modes documented.
- [x] Preserved conversation history used for decisions, incidents and chronology.
- [x] Implemented, superseded, planned and unknown items separated.
- [x] AI-agent continuation guide, rebuild guide, tests and requirement matrix included.
