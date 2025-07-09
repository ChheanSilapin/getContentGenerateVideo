;Video Generator - NSIS Installer Script
;Professional installer with portable support
;Based on NSIS best practices for 2024

;--------------------------------
;Include Modern UI
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

;--------------------------------
;General Configuration
!define APPNAME "Video Generator"
!define APPVERSION "1.0.0"
!define APPCOMPANY "Video Generator Team"
!define APPURL "https://github.com/yourusername/video-generator"
!define APPEXE "VideoGenerator.exe"

;Installer properties
Name "${APPNAME}"
OutFile "VideoGeneratorSetup.exe"
Unicode True
RequestExecutionLevel user  ;No admin required for portable installation

;Default installation directory (user can change)
InstallDir "$LOCALAPPDATA\${APPNAME}"
InstallDirRegKey HKCU "Software\${APPNAME}" "InstallDir"

;Compression
SetCompressor /SOLID lzma
SetCompressorDictSize 32

;--------------------------------
;Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "app_icon.ico"
!define MUI_UNICON "app_icon.ico"

;Header image
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP "installer_header.bmp"  ;Optional: 150x57 pixels
!define MUI_WELCOMEFINISHPAGE_BITMAP "installer_welcome.bmp"  ;Optional: 164x314 pixels

;--------------------------------
;Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"  ;Optional: include license
Page custom InstallOptionsPage InstallOptionsPageLeave
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;--------------------------------
;Languages
!insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Variables
Var CreateDesktopShortcut
Var CreateStartMenuShortcut
Var PortableInstall
Var InstallType

;--------------------------------
;Custom Installation Options Page
Function InstallOptionsPage
    !insertmacro MUI_HEADER_TEXT "Installation Options" "Choose how you want to install ${APPNAME}"
    
    nsDialogs::Create 1018
    Pop $0
    ${If} $0 == error
        Abort
    ${EndIf}
    
    ;Installation type
    ${NSD_CreateLabel} 0 10u 100% 12u "Installation Type:"
    
    ${NSD_CreateRadioButton} 10u 25u 280u 12u "Standard Installation (recommended)"
    Pop $1
    ${NSD_SetState} $1 ${BST_CHECKED}  ;Default selection
    
    ${NSD_CreateRadioButton} 10u 40u 280u 12u "Portable Installation (any folder, no registry)"
    Pop $2
    
    ;Shortcuts section
    ${NSD_CreateGroupBox} 0 65u 100% 60u "Shortcuts"
    
    ${NSD_CreateCheckBox} 10u 80u 280u 12u "Create Desktop shortcut"
    Pop $3
    ${NSD_SetState} $3 ${BST_CHECKED}
    
    ${NSD_CreateCheckBox} 10u 95u 280u 12u "Create Start Menu entry"
    Pop $4
    ${NSD_SetState} $4 ${BST_CHECKED}
    
    ;Information
    ${NSD_CreateLabel} 0 135u 100% 24u "${APPNAME} will work from any location you choose.$\r$\nFirst run will download AI models (requires internet)."
    
    ;Store control handles
    StrCpy $R1 $1  ;Standard radio
    StrCpy $R2 $2  ;Portable radio
    StrCpy $R3 $3  ;Desktop checkbox
    StrCpy $R4 $4  ;Start menu checkbox
    
    nsDialogs::Show
FunctionEnd

Function InstallOptionsPageLeave
    ;Get installation type
    ${NSD_GetState} $R2 $0
    ${If} $0 == ${BST_CHECKED}
        StrCpy $PortableInstall "1"
        StrCpy $InstallType "Portable"
    ${Else}
        StrCpy $PortableInstall "0"
        StrCpy $InstallType "Standard"
    ${EndIf}
    
    ;Get shortcut preferences
    ${NSD_GetState} $R3 $CreateDesktopShortcut
    ${NSD_GetState} $R4 $CreateStartMenuShortcut
    
    ;Disable shortcuts for portable install
    ${If} $PortableInstall == "1"
        StrCpy $CreateStartMenuShortcut ${BST_UNCHECKED}
    ${EndIf}
FunctionEnd

;--------------------------------
;Installation Section
Section "Install" SecInstall
    SetOutPath "$INSTDIR"
    
    ;Copy all files from dist directory
    File /r "dist\VideoGenerator\*.*"
    
    ;Create directories for portable operation
    CreateDirectory "$INSTDIR\models"
    CreateDirectory "$INSTDIR\models\whisper"
    CreateDirectory "$INSTDIR\models\kokoro"
    CreateDirectory "$INSTDIR\config"
    CreateDirectory "$INSTDIR\cache"
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\temp"
    
    ;Create README for users
    FileOpen $0 "$INSTDIR\README.txt" w
    FileWrite $0 "${APPNAME} v${APPVERSION}$\r$\n"
    FileWrite $0 "========================$\r$\n$\r$\n"
    FileWrite $0 "Thank you for installing ${APPNAME}!$\r$\n$\r$\n"
    FileWrite $0 "FIRST RUN:$\r$\n"
    FileWrite $0 "- The first time you run the application, it will download AI models$\r$\n"
    FileWrite $0 "- This requires an internet connection and may take 2-3 minutes$\r$\n"
    FileWrite $0 "- Future runs will be instant$\r$\n$\r$\n"
    FileWrite $0 "PORTABLE INSTALLATION:$\r$\n"
    FileWrite $0 "- You can move this entire folder anywhere$\r$\n"
    FileWrite $0 "- Copy to USB drive for portable use$\r$\n"
    FileWrite $0 "- No registry dependencies$\r$\n$\r$\n"
    FileWrite $0 "SUPPORT:$\r$\n"
    FileWrite $0 "- Visit: ${APPURL}$\r$\n"
    FileClose $0
    
    ;Write installation info (only for standard install)
    ${If} $PortableInstall == "0"
        WriteRegStr HKCU "Software\${APPNAME}" "InstallDir" "$INSTDIR"
        WriteRegStr HKCU "Software\${APPNAME}" "Version" "${APPVERSION}"
        WriteRegStr HKCU "Software\${APPNAME}" "InstallType" "$InstallType"
        
        ;Add to Add/Remove Programs
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${APPVERSION}"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${APPCOMPANY}"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${APPURL}"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
        WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$INSTDIR"
        WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
        WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
        
        ;Estimate size
        ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
        IntFmt $0 "0x%08X" $0
        WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" "$0"
        
        ;Create uninstaller
        WriteUninstaller "$INSTDIR\Uninstall.exe"
    ${EndIf}
    
    ;Create shortcuts
    ${If} $CreateDesktopShortcut == ${BST_CHECKED}
        CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${APPEXE}" "" "$INSTDIR\${APPEXE}" 0
    ${EndIf}
    
    ${If} $CreateStartMenuShortcut == ${BST_CHECKED}
        CreateDirectory "$SMPROGRAMS\${APPNAME}"
        CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${APPEXE}" "" "$INSTDIR\${APPEXE}" 0
        CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
    ${EndIf}
    
SectionEnd

;--------------------------------
;Uninstaller Section
Section "Uninstall"
    ;Remove files
    RMDir /r "$INSTDIR"
    
    ;Remove shortcuts
    Delete "$DESKTOP\${APPNAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APPNAME}"
    
    ;Remove registry entries
    DeleteRegKey HKCU "Software\${APPNAME}"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    
SectionEnd

;--------------------------------
;Functions
Function .onInit
    ;Set default values
    StrCpy $CreateDesktopShortcut ${BST_CHECKED}
    StrCpy $CreateStartMenuShortcut ${BST_CHECKED}
    StrCpy $PortableInstall "0"
    StrCpy $InstallType "Standard"
FunctionEnd
