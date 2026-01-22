@echo off
title Ghost-QC Remote Client

echo.
echo   ____  _               _          ___   ____
echo  / ___^|^| ^|__   ___  ___^| ^|_       / _ \ / ___^|
echo ^| ^|  _ ^| '_ \ / _ \/ __^| __^|_____^| ^| ^| ^| ^|
echo ^| ^|_^| ^|^| ^| ^| ^| (_) \__ \ ^|^|_____^|^| ^|_^| ^| ^|___
echo  \____^|^|_^| ^|_^|\___/^|___/\__^|      \__\_\\____^|
echo.
echo          Remote Client Launcher
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if websockets is installed
python -c "import websockets" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing websockets...
    pip install websockets
)

REM Check if playwright is installed
python -c "import playwright" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing playwright...
    pip install playwright
    echo Installing browser binaries...
    playwright install chromium
)

REM Get server URL
if "%1"=="" (
    set /p SERVER_URL="Enter server URL (e.g., ws://192.168.1.100:8000/api/v1/remote/ws): "
) else (
    set SERVER_URL=%1
)

REM Get client name (optional)
if "%2"=="" (
    set CLIENT_NAME=%COMPUTERNAME%
) else (
    set CLIENT_NAME=%2
)

echo.
echo Starting client...
echo Server: %SERVER_URL%
echo Client Name: %CLIENT_NAME%
echo.

cd /d "%~dp0.."
python -m client.cli --server %SERVER_URL% --name "%CLIENT_NAME%"

pause
