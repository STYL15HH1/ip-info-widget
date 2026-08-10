# IP Info Widget

A lightweight Windows widget that shows your public IP address and connection location.

## Features

- Retrieves connection data securely over HTTPS.
- Shows the public IP, country, a local PNG flag, and optionally the city and internet provider.
- Includes light and dark themes, adjustable opacity, and remembers its position.
- Checks for public IP changes every 5 seconds by default, making VPN server changes visible quickly.
- Displays a Windows notification and saves an IP change history with the old and new IP address, country, and time.
- Copies the IP address to the clipboard when you click it.
- Can be pinned to a selected monitor in a multi-display setup.
- Tests internet access and shows ping latency for a selected host.
- Supports automatic ping checks or a manual connection test from the menu.
- Lets you turn off the always-on-top behavior in Settings.
- Can start automatically when you sign in to Windows.
- Provides a right-click menu with Settings, history, refresh, and exit actions.
- Uses an English interface and English installer.

## Run from source

1. Install Python 3.11 or later for Windows and enable **Add Python to PATH**.
2. Open a terminal in this folder.
3. Run `python -m pip install -r requirements.txt`.
4. Run `python app.py`.

The packages are needed only for system-tray support.

## Flags

The `assets/images/flags` folder contains 252 PNG flag images. The application selects a local file using the country code returned by the API, for example `PL.png` for Poland, without downloading flag images from the internet.

## Build the installer

Install the free [Inno Setup](https://jrsoftware.org/isdl.php) once, then double-click `build_exe.bat` in this folder. The script will:

1. install PyInstaller and required packages on your development computer;
2. include the flag and icon assets;
3. create a standalone `dist/IPInfoWidget.exe`;
4. build `installer/IPInfoWidget-Setup-1.4.1.exe`.

Share `IPInfoWidget-Setup-1.4.1.exe` with end users. They do not need Python or any packages installed. The installer requires UAC confirmation, installs the application in `C:\Program Files\IP Info Widget`, and can create a desktop shortcut.

## Privacy

To obtain the public address and approximate location, the application calls `https://ipwho.is/`. Locally, it stores only appearance and position settings plus up to 50 IP change history records. The history can be cleared from the **IP change history** window.
