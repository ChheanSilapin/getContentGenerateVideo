!include "MUI2.nsh"
Name "Video Generator"
OutFile "dist\Video Generator_Setup_0.0.3.exe"
InstallDir "$PROGRAMFILES\Video Generator"
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"
Section "Install"
    SetOutPath "$INSTDIR"
    File /r "dist\Video Generator\*"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    CreateShortcut "$DESKTOP\Video Generator.lnk" "$INSTDIR\Video Generator.exe"
SectionEnd
Section "Uninstall"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR"
    Delete "$DESKTOP\Video Generator.lnk"
SectionEnd
