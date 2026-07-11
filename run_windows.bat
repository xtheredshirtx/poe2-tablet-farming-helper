@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo Python was not found on PATH.
        echo Install Python 3.10+ from https://www.python.org/downloads/windows/
        echo Make sure "Add python.exe to PATH" is checked during install.
        pause
        exit /b 1
    )
    py -3 main.py
) else (
    python main.py
)

set "APP_EXIT=%ERRORLEVEL%"
if not "%APP_EXIT%"=="0" (
    echo.
    echo The app exited with error code %APP_EXIT%.
    echo If PySide6 is missing, run:
    echo python -m pip install -r requirements.txt
    echo.
    pause
)

exit /b %APP_EXIT%
