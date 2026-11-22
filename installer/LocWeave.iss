; Instalador de LocWeave (Inno Setup). Se genera automáticamente en GitHub Actions.
; No pide permisos de administrador: se instala solo para el usuario actual.
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppName=LocWeave
AppVersion={#AppVersion}
AppPublisher=LocWeave
DefaultDirName={autopf}\LocWeave
DefaultGroupName=LocWeave
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\installer_out
OutputBaseFilename=LocWeave-Setup
SetupIconFile=..\app\gui\assets\icon.ico
UninstallDisplayIcon={app}\LocWeave.exe
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
AppId={{7C1E2B54-3A0D-4D8E-9B53-4C0C5E7A1F21}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; Flags: unchecked

[Files]
Source: "..\dist\LocWeave\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\LocWeave"; Filename: "{app}\LocWeave.exe"
Name: "{autodesktop}\LocWeave"; Filename: "{app}\LocWeave.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\LocWeave.exe"; Description: "Abrir LocWeave"; Flags: nowait postinstall
