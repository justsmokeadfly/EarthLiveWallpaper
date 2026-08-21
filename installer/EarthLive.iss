; EarthLive Wallpaper Inno Setup installer.
;
; The release workflow injects the version from the Git tag before building.

#define MyAppName "EarthLive Wallpaper"
#define MyAppVersion "1.3.0"
#define MyAppAuthor "justsmokeadfly"
#define MyAppURL "https://github.com/justsmokeadfly/EarthLiveWallpaper"
#define MyAppExeName "EarthLive.exe"

[Setup]
AppId={{6C6F3F6F-6A7B-4B8A-9C2D-EARTHLIVE0001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppAuthor}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=output
OutputBaseFilename=EarthLive-Setup-{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; LicenseFile: "..\LICENSE"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"; LicenseFile: "..\LICENSE_RU.txt"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Launch EarthLive Wallpaper automatically at Windows login"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "..\dist\EarthLive\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "EarthLive Wallpaper"; \
    ValueData: """{app}\{#MyAppExeName}"" --headless"; \
    Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\EarthLive Wallpaper\cache"
