;NSIS Modern User Interface
;Multilingual Example Script
;Written by Joost Verburg

; !pragma warning error all
!define TEMP1 $R0 ;Temp variable
!define OPTION_INI "option.ini"

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Properly display all languages (Installer will not work on Windows 95, 98 or ME!)
  Unicode true

  ;Name and file
  Name "Java Development Kit Version Manager"
  OutFile "Stetup.exe"

  ;Default installation folder
  InstallDir "$LOCALAPPDATA\jdkmgr"
  
  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\Java Development Kit Version Manager" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel admin

  ;Show install details dialog box when installing
  ShowInstDetails Show

  ;Load option plugin
  ReserveFile /plugin InstallOptions.dll
  ReserveFile "${OPTION_INI}"

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

  ;Show all languages, despite user's codepage
  !define MUI_LANGDLL_ALLLANGUAGES

;--------------------------------
;Language Selection Dialog Settings

  ;Remember the installer language
  !define MUI_LANGDLL_REGISTRY_ROOT "HKCU" 
  !define MUI_LANGDLL_REGISTRY_KEY "Software\Java Development Kit Version Manager" 
  !define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_LICENSE "${NSISDIR}\Docs\Modern UI\License.txt"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  Page custom SetCustom ValidateCustom ": Testing InstallOptions" ;Custom page. InstallOptions gets called in SetCustom.
  !insertmacro MUI_PAGE_FINISH
  
  !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_LICENSE "${NSISDIR}\Docs\Modern UI\License.txt"
  !insertmacro MUI_UNPAGE_COMPONENTS
  !insertmacro MUI_UNPAGE_DIRECTORY
  !insertmacro MUI_UNPAGE_INSTFILES
  !insertmacro MUI_UNPAGE_FINISH


;--------------------------------
;Languages
  !include "lan.nsh"
;--------------------------------
;Reserve Files
  
  ;If you are using solid compression, files that are required before
  ;the actual installation should be stored first in the data block,
  ;because this will make your installer start faster.
  
  !insertmacro MUI_RESERVEFILE_LANGDLL

;--------------------------------
;Installer Sections

Section "Main" SecMain

  SetOutPath "$INSTDIR"
  
  ;ADD YOUR OWN FILES HERE...
  File /r "..\source"
  ;Store installation folder
  WriteRegStr HKCU "Software\Java Development Kit Version Manager" "" $INSTDIR
  
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  SetOutPath "$INSTDIR\bin"
  File /r "..\dist\jdkmgr.dist\"

SectionEnd

;--------------------------------
;Installer Functions

Function .onInit

  !insertmacro MUI_LANGDLL_DISPLAY
  InitPluginsDir
  File /oname=$PLUGINSDIR\option.ini "${OPTION_INI}"

FunctionEnd

;--------------------------------
;Set Custom Options

Function SetCustom

  Push ${TEMP1}

    InstallOptions::dialog "$PLUGINSDIR\option.ini"
    Pop ${TEMP1}
  
  Pop ${TEMP1}

FunctionEnd

;--------------------------------
;Verify Custom Options

Function ValidateCustom
  ReadINIStr ${TEMP1} "$PLUGINSDIR\option.ini" "Field 1" "State"
  StrCmp ${TEMP1} 1 add_java_path

  add_java_path:
    EnVar::SetHKLM

    EnVar::AddValue "JAVA_HOME" "$INSTDIR\jdk"

    Goto done

  done:
FunctionEnd

;--------------------------------
;Descriptions

  ;USE A LANGUAGE STRING IF YOU WANT YOUR DESCRIPTIONS TO BE LANGAUGE SPECIFIC

  ;Assign descriptions to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(MAIN_INFO)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END


;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;ADD YOUR OWN FILES HERE...

  RMDir /r "$INSTDIR"

  DeleteRegKey /ifempty HKCU "Software\Java Development Kit Version Manager"

SectionEnd

;--------------------------------
;Uninstaller Functions

Function un.onInit

  !insertmacro MUI_UNGETLANGUAGE
  
FunctionEnd