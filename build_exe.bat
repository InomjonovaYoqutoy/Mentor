@echo off
setlocal
cd /d "%~dp0"
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :fail
python -m PyInstaller --noconfirm --clean --windowed --name Mentor --collect-all PySide6 main.py
if errorlevel 1 goto :fail
echo.
echo Build complete: dist\Mentor\Mentor.exe
exit /b 0
:fail
echo.
echo Build failed. Review the errors above.
pause
exit /b 1