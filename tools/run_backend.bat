@echo off
REM Runs the PolicyGPT API and restarts it automatically if it ever stops unexpectedly.
title PolicyGPT backend
cd /d "%~dp0..\backend"
:loop
echo [%date% %time%] Starting PolicyGPT backend on http://localhost:8000 ...
"..\.venv\Scripts\python.exe" run.py
echo.
echo [%date% %time%] Backend stopped (exit code %errorlevel%). Restarting in 5 seconds - close this window to stop it.
timeout /t 5 /nobreak >nul
goto loop
