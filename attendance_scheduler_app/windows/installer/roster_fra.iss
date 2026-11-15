; Windows installer for the Roster FRA desktop client (Inno Setup 6).
; Built by .github/workflows/desktop-release.yml:
;   iscc /DAppVersion=1.0.0.123 /DSourceDir=<Release folder> roster_fra.iss
; Installs per user (no admin prompt), adds Start menu and desktop
; shortcuts, and upgrades in place: the app's own updater runs it with
; /VERYSILENT and it starts the app again when done.

#ifndef AppVersion
  #define AppVersion "1.0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\..\build\windows\x64\runner\Release"
#endif

[Setup]
AppId={{6F1B1D52-9C1E-4F7B-9E1C-6A0F2D8E4B11}
AppName=Roster FRA
AppVersion={#AppVersion}
AppPublisher=Vietnam Airlines FRA
DefaultDirName={localappdata}\Programs\Roster FRA
DefaultGroupName=Roster FRA
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=RosterFRA-Setup
SetupIconFile=..\runner\resources\app_icon.ico
UninstallDisplayIcon={app}\attendance_scheduler_app.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=force
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Roster FRA"; Filename: "{app}\attendance_scheduler_app.exe"
Name: "{autodesktop}\Roster FRA"; Filename: "{app}\attendance_scheduler_app.exe"; Tasks: desktopicon

[Run]
; Interactive install: offer to start the app. Silent update (from the app):
; start it again without asking.
Filename: "{app}\attendance_scheduler_app.exe"; Description: "{cm:LaunchProgram,Roster FRA}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\attendance_scheduler_app.exe"; Flags: nowait; Check: WizardSilent
