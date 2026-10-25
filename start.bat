@echo off
setlocal

REM 1. Check py launcher
where py >nul 2>nul
if %errorlevel% equ 0 (
    set PYCMD=py
    goto python_found
)

REM 2. Check python in PATH
where python >nul 2>nul
if %errorlevel% equ 0 (
    set PYCMD=python
    goto python_found
)

REM 3. Check Python in User LocalAppData
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set "PYCMD=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    goto python_found
)
if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python314\python.exe" (
    set "PYCMD=%USERPROFILE%\AppData\Local\Programs\Python\Python314\python.exe"
    goto python_found
)

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%D\python.exe" (
        set "PYCMD=%%D\python.exe"
        goto python_found
    )
)

echo [ERROR] Python installation was not detected in PATH or User directory.
echo Please install Python 3.10+ from python.org
pause
exit /b 1

:python_found
if /i "%~1"=="test" (
    "%PYCMD%" -m pytest tests/ -v
    pause
    exit /b %errorlevel%
)

cls
echo ======================================================================
echo    NISABA — High-Performance Sumerian Epigraphic Computational Engine
echo ======================================================================
echo.
echo   🚀 Starting Nisaba backend and launching web explorer in browser...
echo.
echo      • Visual Tablet Explorer : http://127.0.0.1:8000/explorer
echo      • Prosopography Graph    : http://127.0.0.1:8000/api/graph/view
echo      • REST API / SQL Console : http://127.0.0.1:8000/docs
echo      • One-Page User Manual   : docs/USER_MANUAL.md
echo.
echo   (Keep this window open. Press Ctrl+C to stop the server)
echo ======================================================================
echo.

start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000/explorer"

"%PYCMD%" scripts/run_api.py --port 8000 --host 127.0.0.1
