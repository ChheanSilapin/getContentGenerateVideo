; ================================================================================================
; Video Generator - Professional Inno Setup Installer Script
; Version: 0.0.3
; Description: Complete installer with all professional features
; ================================================================================================

#define MyAppName "Video Generator"
#define MyAppVersion "0.0.3"
#define MyAppPublisher "Video Generator Team"
#define MyAppURL "https://github.com/yourusername/videogenerator"
#define MyAppExeName "Video Generator.exe"
#define MyAppAssocName MyAppName + " Video Project"
#define MyAppAssocExt ".vgp"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{A7B8C9D0-E1F2-4A5B-9C8D-7E6F5A4B3C2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
ChangesAssociations=yes
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
InfoBeforeFile=README.md
OutputDir=dist
OutputBaseFilename={#MyAppName}_Setup_{#MyAppVersion}
SetupIconFile=app_icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoCopyright=Copyright (C) 2024 {#MyAppPublisher}
ShowLanguageDialog=no
AppReadmeFile={app}\README.txt
WizardImageFile=compiler:WizModernImage-IS.bmp
WizardSmallImageFile=compiler:WizModernSmallImage-IS.bmp

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "armenian"; MessagesFile: "compiler:Languages\Armenian.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "catalan"; MessagesFile: "compiler:Languages\Catalan.isl"
Name: "corsican"; MessagesFile: "compiler:Languages\Corsican.isl"
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"
Name: "danish"; MessagesFile: "compiler:Languages\Danish.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "icelandic"; MessagesFile: "compiler:Languages\Icelandic.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "slovenian"; MessagesFile: "compiler:Languages\Slovenian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "associatewithfiles"; Description: "&Associate with Video Generator project files"; GroupDescription: "File associations:"; Flags: unchecked
Name: "addtopath"; Description: "Add {#MyAppName} to PATH environment variable"; GroupDescription: "System integration:"; Flags: unchecked

[Types]
Name: "full"; Description: "Full installation"
Name: "compact"; Description: "Compact installation"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "main"; Description: "Core application files"; Types: full compact custom; Flags: fixed
Name: "ffmpeg"; Description: "FFmpeg video processing tools (Required)"; Types: full compact custom; Flags: fixed
Name: "docs"; Description: "Documentation and guides"; Types: full custom
Name: "fonts"; Description: "Additional fonts for better typography"; Types: full custom
Name: "examples"; Description: "Example projects and templates"; Types: full custom; Check: DirExists(ExpandConstant('{src}\examples'))

[Dirs]
Name: "{app}"; Permissions: users-full
Name: "{userappdata}\{#MyAppName}"; Permissions: users-full
Name: "{userappdata}\{#MyAppName}\Projects"; Permissions: users-full
Name: "{userappdata}\{#MyAppName}\Output"; Permissions: users-full
Name: "{userappdata}\{#MyAppName}\Temp"; Permissions: users-full

[Files]
; ================================================================================================
; CORE APPLICATION FILES (Required)
; ================================================================================================
Source: "dist\Video Generator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main
Source: "dist\Video Generator\Video Generator.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: main

; ================================================================================================
; FFMPEG BINARIES (Critical for video processing)
; ================================================================================================
Source: "ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: ffmpeg; Check: FileExists(ExpandConstant('{src}\ffmpeg.exe'))
Source: "ffplay.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: ffmpeg; Check: FileExists(ExpandConstant('{src}\ffplay.exe'))
Source: "ffprobe.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: ffmpeg; Check: FileExists(ExpandConstant('{src}\ffprobe.exe'))

; ================================================================================================
; DOCUMENTATION AND GUIDES
; ================================================================================================
Source: "README.md"; DestDir: "{app}"; DestName: "README.txt"; Flags: ignoreversion; Components: docs; Check: FileExists(ExpandConstant('{src}\README.md'))
Source: "SUBTITLE_CONFIG_GUIDE.md"; DestDir: "{app}"; DestName: "Subtitle_Configuration_Guide.txt"; Flags: ignoreversion; Components: docs; Check: FileExists(ExpandConstant('{src}\SUBTITLE_CONFIG_GUIDE.md'))
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion; Components: docs; Check: FileExists(ExpandConstant('{src}\LICENSE.txt'))

; ================================================================================================
; APPLICATION ASSETS
; ================================================================================================
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{src}\app_icon.ico'))

; ================================================================================================
; FONTS (Optional but recommended)
; ================================================================================================
Source: "fonts\*"; DestDir: "{app}\fonts"; Flags: ignoreversion recursesubdirs; Components: fonts; Check: DirExists(ExpandConstant('{src}\fonts'))

; ================================================================================================
; EXAMPLE PROJECTS (Optional)
; ================================================================================================
Source: "examples\*"; DestDir: "{userappdata}\{#MyAppName}\Examples"; Flags: ignoreversion recursesubdirs; Components: examples; Check: DirExists(ExpandConstant('{src}\examples'))

[Registry]
; ================================================================================================
; APPLICATION REGISTRY ENTRIES
; ================================================================================================
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "ExecutablePath"; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey

; ================================================================================================
; FILE ASSOCIATION REGISTRY ENTRIES
; ================================================================================================
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associatewithfiles
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey; Tasks: associatewithfiles
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: associatewithfiles
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: associatewithfiles
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".vgp"; ValueData: ""; Tasks: associatewithfiles

; ================================================================================================
; PATH ENVIRONMENT VARIABLE
; ================================================================================================
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath('{app}')

[Icons]
; ================================================================================================
; START MENU SHORTCUTS
; ================================================================================================
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Comment: "Create videos with subtitles from text and images"
Name: "{group}\Documentation\User Guide"; Filename: "{app}\README.txt"; Comment: "Read the user guide"
Name: "{group}\Documentation\Subtitle Configuration Guide"; Filename: "{app}\Subtitle_Configuration_Guide.txt"; Comment: "Learn how to configure subtitles"; Check: FileExists(ExpandConstant('{app}\Subtitle_Configuration_Guide.txt'))
Name: "{group}\Tools\Open Output Folder"; Filename: "{userappdata}\{#MyAppName}\Output"; Comment: "Open the default output folder"
Name: "{group}\Tools\Open Projects Folder"; Filename: "{userappdata}\{#MyAppName}\Projects"; Comment: "Open the projects folder"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; Comment: "Uninstall {#MyAppName}"

; ================================================================================================
; DESKTOP AND QUICK LAUNCH SHORTCUTS
; ================================================================================================
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Comment: "Create videos with subtitles"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: quicklaunchicon

[Run]
; ================================================================================================
; POST-INSTALLATION ACTIONS
; ================================================================================================
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\README.txt"; Description: "View the User Guide"; Flags: nowait postinstall skipifsilent unchecked shellexec
Filename: "https://github.com/yourusername/videogenerator"; Description: "Visit the project website"; Flags: nowait postinstall skipifsilent unchecked shellexec

[UninstallRun]
; ================================================================================================
; PRE-UNINSTALL CLEANUP
; ================================================================================================
Filename: "{cmd}"; Parameters: "/C ""taskkill /f /im ""{#MyAppExeName}"" & exit"""; RunOnceId: "KillMyApp"; Flags: runhidden

[UninstallDelete]
; ================================================================================================
; UNINSTALL CLEANUP
; ================================================================================================
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{userappdata}\{#MyAppName}\Temp"

[Code]
; ================================================================================================
; CUSTOM PASCAL SCRIPT FUNCTIONS
; ================================================================================================

// Function to check if PATH addition is needed
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  // look for the path with leading and trailing semicolon
  // Pos() returns 0 if not found
  Result := Pos(';' + UpperCase(Param) + ';', ';' + UpperCase(OrigPath) + ';') = 0;
end;

// Function to check system requirements
function InitializeSetup(): Boolean;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  
  // Check Windows version (Windows 10 or later)
  if Version.Major < 10 then
  begin
    MsgBox('This application requires Windows 10 or later. Setup will now exit.', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;

// Custom page for additional options
var
  OptionsPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  // Create custom options page
  OptionsPage := CreateInputQueryPage(wpSelectTasks,
    'Additional Options', 'Configure additional installation options',
    'Please specify additional options for Video Generator installation:');
    
  OptionsPage.Add('Default output folder:', False);
  OptionsPage.Values[0] := ExpandConstant('{userdocs}\Video Generator Output');
  
  OptionsPage.Add('Maximum video cache size (MB):', False);
  OptionsPage.Values[1] := '1024';
end;

// Save custom settings to registry
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Save custom settings
    RegWriteStringValue(HKEY_CURRENT_USER, 'Software\{#MyAppPublisher}\{#MyAppName}', 
      'DefaultOutputPath', OptionsPage.Values[0]);
    RegWriteStringValue(HKEY_CURRENT_USER, 'Software\{#MyAppPublisher}\{#MyAppName}', 
      'MaxCacheSize', OptionsPage.Values[1]);
      
    // Create output directory
    ForceDirectories(ExpandConstant(OptionsPage.Values[0]));
  end;
end;

// Custom messages and finishing page
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    WizardForm.FinishedLabel.Caption := 
      'Video Generator has been successfully installed!' + #13#13 +
      'Key Features:' + #13 +
      '• Generate videos from text and images' + #13 +
      '• Automatic subtitle generation' + #13 +
      '• Professional video effects' + #13 +
      '• Batch processing capabilities' + #13 +
      '• Video merging functionality' + #13#13 +
      'Click Finish to complete the installation.';
  end;
end;

// Check for existing installation
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  
  // Skip license page if upgrading
  if (PageID = wpLicense) and (WizardSilent()) then
    Result := True;
end;

[Messages]
; ================================================================================================
; CUSTOM MESSAGES
; ================================================================================================
WelcomeLabel2=This will install [name/ver] on your computer.%n%nVideo Generator is a powerful application for creating videos with subtitles from text and images. It includes automated text-to-speech, image processing, and professional video effects.%n%nIt is recommended that you close all other applications before continuing.
ClickNext=Click Next to continue, or Cancel to exit Setup.
BeveledLabel=Video Generator - Professional Video Creation Tool 