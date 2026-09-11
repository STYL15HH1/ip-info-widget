; IP Info Widget installer.
; Run build_exe.bat first to create dist\IPInfoWidget-<version>.exe.

#define MyAppName "IP Info Widget"
; build_exe.bat forwards core.version.APP_VERSION to this script.
; The fallback permits a direct compile when Python is unavailable.
#ifndef MyAppVersion
  #define MyAppVersion "1.5.1"
#endif
#define MyAppPublisher "IP Info Widget"
#define MyAppExeName "IPInfoWidget-" + MyAppVersion + ".exe"

#ifndef BuildDir
  #define BuildDir "dist"
#endif

[Setup]
AppId={{E9E2C4C3-B19D-4B5B-942C-AD76CA3CF5B6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
UsePreviousAppDir=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=IPInfoWidget-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=assets\icons\ip-info-widget.ico
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.CreateDesktopShortcut=Create a desktop shortcut
english.AdditionalShortcuts=Additional shortcuts:
english.LaunchApplication=Launch %1

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopShortcut}"; GroupDescription: "{cm:AdditionalShortcuts}"; Flags: unchecked

[Files]
Source: "{#BuildDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchApplication,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
