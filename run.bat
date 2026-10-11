@echo off
REM ============================================================
REM  V.A.S.U.K.I. one-click launcher for Windows
REM  Double-click this file (or run it from a terminal).
REM  It sets up everything, starts the server, and opens the
REM  game in your browser at http://127.0.0.1:5000
REM ============================================================

setlocal enableextensions
cd /d "%~dp0"

echo(
echo ==== V.A.S.U.K.I. launcher ====
echo(

REM ---- 1. Locate Python -------------------------------------
set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo [ERROR] Python was not found on this machine.
    echo         Install Python 3 from https://www.python.org/downloads/
    echo         and be sure to tick "Add python.exe to PATH".
    echo(
    pause
    exit /b 1
)
echo Using Python launcher: %PY%

REM ---- 2. Create virtual environment (first run only) -------
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment ^(.venv^) ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

set "VENV_PY=.venv\Scripts\python.exe"

REM ---- 3. Ensure Flask is installed -------------------------
"%VENV_PY%" -c "import flask" >nul 2>nul
if errorlevel 1 (
    echo Installing Flask ^(first-time setup^) ...
    "%VENV_PY%" -m pip install --upgrade pip >nul 2>nul
    "%VENV_PY%" -m pip install flask
    if errorlevel 1 (
        echo [ERROR] Could not install Flask. Check your internet connection.
        pause
        exit /b 1
    )
)

REM ---- 4. Open the browser shortly after the server starts --
echo Opening http://127.0.0.1:5000 in your browser ...
start "" /b cmd /c "timeout /t 3 >nul & start "" http://127.0.0.1:5000"

REM ---- 5. Start the game server (this window stays open) ----
echo(
echo Server starting. Keep this window open while you play.
echo Press CTRL+C here to stop the game.
echo(
set "VASUKI_LAUNCHER=1"
"%VENV_PY%" app.py

echo(
echo Server stopped.
pause
endlocal
