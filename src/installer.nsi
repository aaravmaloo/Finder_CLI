!include "MUI2.nsh"

Name "Finder_CLI"
OutFile "Finder_CLI_Setup.exe"
InstallDir "$PROGRAMFILES\Finder_CLI"
RequestExecutionLevel admin

!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"

    ; Copy Rust executable
    File /r "dist\rust_src.exe"

    ; Copy DLL if it exists
    File /nonfatal "dist\rust_src.dll"

    ; Copy Python runtime if needed
    File /nonfatal "src\.venv\Scripts\python.exe"

    ; Rename executable
    Rename "$INSTDIR\rust_src.exe" "$INSTDIR\finder_cli.exe"

    ; Add to system PATH
    EnVar::SetHKLM
    EnVar::AddValue "Path" "$INSTDIR"

    ; Create an index file
    SetOutPath "$PROFILE"
    FileOpen $0 "$PROFILE\index.txt" w
    FileWrite $0 "This is the index.txt file created by Finder_CLI installer."
    FileClose $0
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\finder_cli.exe"
    Delete "$INSTDIR\rust_src.dll"

    RMDir /r "$INSTDIR"

    ; Remove from PATH
    EnVar::SetHKLM
    EnVar::DeleteValue "Path" "$INSTDIR"

    ; Delete index file
    Delete "$PROFILE\index.txt"
SectionEnd  ; <<--- This was missing, causing the error!
