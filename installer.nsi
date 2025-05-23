
; Video Generator Installer Script
!include "MUI2.nsh"

; General
Name "Video Generator"
OutFile "dist/Video Generator_Setup_1.0.0.exe"
InstallDir "$PROGRAMFILES\Video Generator"
InstallDirRegKey HKCU "Software\Video Generator" ""

; Interface Settings
!define MUI_ABORTWARNING

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer Sections
Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Add files
    File /r "dist\Video Generator\*.*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\Video Generator"
    CreateShortcut "$SMPROGRAMS\Video Generator\Video Generator.lnk" "$INSTDIR\Video Generator.exe"
    CreateShortcut "$SMPROGRAMS\Video Generator\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortcut "$DESKTOP\Video Generator.lnk" "$INSTDIR\Video Generator.exe"
    
    ; Write registry keys
    WriteRegStr HKCU "Software\Video Generator" "" $INSTDIR
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video Generator" "DisplayName" "Video Generator"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video Generator" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video Generator" "DisplayIcon" "$\"$INSTDIR\Video Generator.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video Generator" "DisplayVersion" "1.0.0"
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ; Remove files and directories
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\Video Generator\Video Generator.lnk"
    Delete "$SMPROGRAMS\Video Generator\Uninstall.lnk"
    RMDir "$SMPROGRAMS\Video Generator"
    Delete "$DESKTOP\Video Generator.lnk"
    
    ; Remove registry keys
    DeleteRegKey HKCU "Software\Video Generator"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Video Generator"
SectionEnd
    