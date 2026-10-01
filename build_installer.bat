@echo off
setlocal
cd /d "%~dp0"

call build_exe.bat
if errorlevel 1 goto :fail

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo.
  echo Inno Setup 6 was not found.
  echo Install it from https://jrsoftware.org/isinfo.php and run this file again.
  exit /b 1
)

"%ISCC%" "installer\Mentor.iss"
if errorlevel 1 goto :fail

echo.
echo Installer ready: dist\installer\MentorSetup.exe
exit /b 0

:fail
echo.
echo Installer build failed. Review the errors above.
exit /b 1
