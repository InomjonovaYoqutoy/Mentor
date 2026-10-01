@echo off
setlocal
cd /d "%~dp0"
echo [1/2] Compiling Mentor...
python -m compileall -q mentor tests
if errorlevel 1 goto :fail
echo [2/2] Running database, regression, and Qt smoke tests...
set QT_QPA_PLATFORM=offscreen
python -m unittest discover -s tests -p "test_*.py" -v
if errorlevel 1 goto :fail
echo.
echo Quality check passed.
exit /b 0
:fail
echo.
echo Quality check failed. Do not ship this build.
pause
exit /b 1